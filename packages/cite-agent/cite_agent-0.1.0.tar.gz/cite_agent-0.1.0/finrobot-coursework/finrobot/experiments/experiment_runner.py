"""
Comprehensive experiment runner for comparing FinRobot vs RAG.

Orchestrates:
1. Running agents on various stocks and tasks
2. Collecting rich metrics (latency, cost, reasoning depth, accuracy)
3. Fact-checking predictions via web browsing
4. Exporting results for analysis
"""

import time
import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from textwrap import dedent

import autogen
from autogen import AssistantAgent, UserProxyAgent, register_function

from finrobot.utils import get_current_date
from finrobot.data_source import YFinanceUtils
from finrobot.logging import get_logger
from finrobot.experiments.metrics_collector import MetricsCollector, MetricSnapshot
from finrobot.experiments.fact_checker import FactChecker

logger = get_logger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for an experiment run."""

    name: str
    tickers: List[str]
    tasks: List[Dict[str, str]]  # List of {"name": str, "prompt": str}
    system: str  # "agent" or "rag"
    llm_model: str = "gpt-4"
    temperature: float = 0.2
    max_retries: int = 3
    timeout_seconds: float = 120.0
    verify_predictions: bool = True


@dataclass
class ExperimentTask:
    """Single task to execute in an experiment."""

    name: str
    prompt: str
    ticker: str
    system: str


class FinRobotExperimentRunner:
    """
    Runs FinRobot agent on stocks and collects metrics.
    
    Measures:
    - Latency (response time)
    - Cost (API tokens)
    - Reasoning depth (tool calls, chain of thought)
    - Output quality (length, claims made)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize runner.
        
        Args:
            config: OpenAI config dict or path to config file
        """
        self.config_file = config or "OAI_CONFIG_LIST"
        self.metrics = MetricsCollector()
        self.fact_checker = FactChecker()
        logger.info("FinRobotExperimentRunner initialized")

    def _get_config_list(self, model: str):
        """Load OpenAI config for specified model."""
        try:
            return autogen.config_list_from_json(
                self.config_file, filter_dict={"model": [model]}
            )
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def run_agent_analysis(
        self,
        ticker: str,
        task_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.2,
        task_name: str = "analysis",
    ) -> MetricSnapshot:
        """
        Run FinRobot agent on a stock analysis task.
        
        Args:
            ticker: Stock symbol
            task_prompt: Full task prompt for agent
            model: LLM model to use
            temperature: LLM temperature
            task_name: Name of task for tracking
            
        Returns:
            MetricSnapshot with results and metrics
        """
        experiment_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        metric = self.metrics.start_measurement(
            experiment_id=experiment_id,
            system_name="agent",
            ticker=ticker,
            task_name=task_name,
        )

        try:
            config_list = self._get_config_list(model)
            llm_config = {
                "config_list": config_list,
                "timeout": 120,
                "temperature": temperature,
            }

            # Create agents
            assistant = AssistantAgent(
                "Market_Analyst",
                system_message=dedent("""
                    You are a Market Analyst. Analyze the stock data provided to you.
                    Use the provided tools to gather comprehensive information.
                    Provide specific, data-driven analysis.
                    Reply TERMINATE when analysis is complete.
                """),
                llm_config=llm_config,
            )

            user_proxy = UserProxyAgent(
                "User_Proxy",
                human_input_mode="NEVER",
                max_consecutive_auto_reply=15,
                is_termination_msg=lambda x: x.get("content", "")
                and x.get("content", "").endswith("TERMINATE"),
                code_execution_config={"work_dir": "coding", "use_docker": False},
            )

            # Register tools
            def get_stock_data_wrapper(
                symbol: str, start_date: str, end_date: str, save_path: str = ""
            ) -> str:
                """Retrieve stock price data for designated ticker symbol."""
                try:
                    result = YFinanceUtils.get_stock_data(
                        symbol, start_date, end_date, save_path or None
                    )
                    return str(result)
                except Exception as e:
                    logger.error(f"Error fetching stock data: {e}")
                    return f"Error: {str(e)}"

            register_function(
                get_stock_data_wrapper,
                caller=assistant,
                executor=user_proxy,
                name="get_stock_data",
                description="Retrieve stock price data for a ticker",
            )

            # Run agent
            logger.info(f"Starting agent analysis for {ticker}")
            
            # Capture conversation for metrics
            conversation = []
            original_send = user_proxy.send

            def tracking_send(message, recipient, **kwargs):
                nonlocal conversation
                conversation.append({"role": "user", "content": message})
                return original_send(message, recipient, **kwargs)

            user_proxy.send = tracking_send

            user_proxy.initiate_chat(assistant, message=task_prompt, cache=None)

            # Extract response from last message
            if hasattr(assistant, "last_message") and assistant.last_message:
                response = assistant.last_message.get("content", "")
            else:
                response = "No response generated"

            metric.set_response(response)
            
            # Estimate tool calls from conversation
            metric.tool_calls_count = sum(
                1 for msg in conversation if "get_stock_data" in str(msg)
            )
            metric.reasoning_steps = len(conversation)

            # TODO: Track actual token usage from API
            # For now, estimate
            metric.set_cost(
                prompt_tokens=len(task_prompt.split()) * 2,
                completion_tokens=len(response.split()) * 2,
                model=model,
            )

            logger.info(
                f"Agent analysis complete for {ticker}: {metric.tool_calls_count} tools, {metric.latency_seconds:.2f}s"
            )

        except Exception as e:
            logger.error(f"Agent analysis failed for {ticker}: {e}")
            metric.error_occurred = True
            metric.error_message = str(e)

        finally:
            self.metrics.end_measurement(metric)

        return metric

    def run_multiple_experiments(
        self,
        tickers: List[str],
        tasks: List[Dict[str, str]],
        system: str = "agent",
        model: str = "gpt-4",
    ) -> List[MetricSnapshot]:
        """
        Run multiple experiments systematically.
        
        Args:
            tickers: List of stock symbols
            tasks: List of task dicts with "name" and "prompt"
            system: "agent" or "rag"
            model: LLM model
            
        Returns:
            List of all MetricSnapshots
        """
        results = []
        total = len(tickers) * len(tasks)
        current = 0

        for ticker in tickers:
            for task in tasks:
                current += 1
                print(
                    f"\n[{current}/{total}] Running {system} on {ticker} - {task['name']}"
                )

                try:
                    if system == "agent":
                        metric = self.run_agent_analysis(
                            ticker=ticker,
                            task_prompt=task["prompt"],
                            model=model,
                            task_name=task["name"],
                        )
                    else:
                        logger.warning(f"System '{system}' not yet implemented")
                        continue

                    results.append(metric)

                except Exception as e:
                    logger.error(f"Failed on {ticker}/{task['name']}: {e}")
                    continue

        return results

    def export_results(self, filename: Optional[str] = None) -> str:
        """
        Export all metrics to CSV.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to exported file
        """
        path = self.metrics.export_csv(filename)
        logger.info(f"Exported results to {path}")
        return str(path)

    def print_summary(self):
        """Print human-readable summary."""
        self.metrics.print_summary()


def create_standard_tasks() -> List[Dict[str, str]]:
    """
    Create standard set of analysis tasks for comparison.
    
    Returns:
        List of task dicts
    """
    return [
        {
            "name": "price_prediction",
            "prompt": dedent(f"""
                Analyze the stock data I'm about to provide.
                Predict the stock price movement for the next week (up/down by what %?).
                Provide specific reasoning based on the data.
                Reply TERMINATE when done.
            """),
        },
        {
            "name": "risk_analysis",
            "prompt": dedent(f"""
                Analyze the recent stock data.
                Identify the top 2-3 risk factors based on price movements and volatility.
                Be specific with numbers and time periods.
                Reply TERMINATE when done.
            """),
        },
        {
            "name": "opportunity_search",
            "prompt": dedent(f"""
                Analyze the stock data.
                Identify 2-3 investment opportunities based on technical and price patterns.
                Provide specific reasoning.
                Reply TERMINATE when done.
            """),
        },
    ]


if __name__ == "__main__":
    # Example usage
    from textwrap import dedent

    runner = FinRobotExperimentRunner()

    # Test on 3 stocks
    tickers = ["AAPL", "MSFT", "TSLA"]
    tasks = create_standard_tasks()

    logger.info(f"Starting experiments on {len(tickers)} stocks with {len(tasks)} tasks")

    # Run agent experiments
    results = runner.run_multiple_experiments(
        tickers=tickers,
        tasks=tasks,
        system="agent",
        model="gpt-4",
    )

    # Export and summarize
    runner.export_results()
    runner.print_summary()

    logger.info(f"Completed {len(results)} experiments")
