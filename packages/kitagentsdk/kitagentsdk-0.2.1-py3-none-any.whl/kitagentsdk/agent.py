# src/kitagentsdk/agent.py
import json
import os
import sys
import atexit
from pathlib import Path
from abc import ABC, abstractmethod
from .kit import KitClient
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.vec_env import VecEnv

class BaseAgent(ABC):
    """Abstract base class for all Kit agents."""

    def __init__(self, config_path: str, output_path: str):
        self.output_path = Path(output_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}

        self.is_test_run = False # Flag to indicate if running in test/simulation mode
        
        self.kit = KitClient()
        self.kit.agent = self  # Give KitClient a reference back to the agent
        
        # Ensure telemetry is flushed on exit
        atexit.register(self.kit.shutdown)

        if self.kit.enabled and self.kit.run_id:
            self.emit_event("SDK_INITIALIZED")

    def log(self, message: str):
        """Logs a message, sending it to the backend via KitClient if available."""
        # Don't strip internal newlines, just trailing whitespace to avoid double spacing
        message = message.rstrip()
        if not message: return
        # Explicitly append newline for the persistent log
        self.kit.log_message(message + "\n")

    def emit_event(self, event_name: str, status: str = "info"):
        """Emits a lifecycle event."""
        self.kit.log_event(event_name, status)

    def report_progress(self, step: int):
        """Reports the current training step."""
        self.kit.log_progress(step)
        
        # Fallback for local legacy debugging
        progress_file = self.output_path / "progress.log"
        with open(progress_file, "w") as f:
            f.write(str(step))

    def record_metric(self, name: str, step: int, value: float):
        """Records a key-step-value metric."""
        self.kit.log_metric(name, step, value)

    def orchestrate_sb3_training(
        self,
        env: VecEnv,
        model: BaseAlgorithm,
        is_new_model: bool,
        total_timesteps: int,
        custom_callbacks: list = None,
    ):
        """
        Handles the complete, standardized training lifecycle for a Stable Baselines 3 model.
        """
        final_model_path = self.output_path / "model.zip"
        temp_model_path = self.output_path / "model_temp.zip"
        norm_stats_path = self.output_path / "norm_stats.json"

        from stable_baselines3.common.callbacks import CallbackList
        from .callbacks import InterimSaveCallback, KitLogCallback, SB3MetricsCallback

        checkpoint_freq = self.config.get("checkpoint_freq", 10000)
        
        progress_offset = 0
        if not is_new_model:
            progress_offset = model.num_timesteps

        callbacks = [
            InterimSaveCallback(save_path=str(temp_model_path), save_freq=checkpoint_freq),
            KitLogCallback(offset=progress_offset),
            SB3MetricsCallback(),
        ]
        if custom_callbacks:
            callbacks.extend(custom_callbacks)

        try:
            self.emit_event("TRAINING_LOOP_STARTED")
            model.learn(
                total_timesteps=total_timesteps,
                reset_num_timesteps=is_new_model,
                tb_log_name="swing_agent_run",
                callback=CallbackList(callbacks),
            )
            self.emit_event("TRAINING_LOOP_COMPLETED", "success")

            self.emit_event("MODEL_SAVING_STARTED")
            model.save(final_model_path)
            self.kit.upload_artifact(str(final_model_path), "model")
            self.emit_event("MODEL_SAVED", "success")

            if is_new_model:
                with open(norm_stats_path, 'w') as f:
                    json.dump(env.envs[0].unwrapped.get_norm_stats(), f, indent=4)
                self.kit.upload_artifact(str(norm_stats_path), "normalization_stats")
                self.log(f"Saved normalization stats to {norm_stats_path}")
            
            if os.path.exists(temp_model_path):
                os.remove(temp_model_path)

        except KeyboardInterrupt:
            self.log("--- 🛑 Training interrupted by user. ---")
            sys.exit(0) # Graceful exit on Ctrl+C
        except Exception as e:
            self.log(f"--- ❌ An unexpected error occurred during training: {e} ---")
            self.emit_event("AGENT_TRAINING_FAILED", "failure")
            raise e

    @abstractmethod
    def train(self):
        """The main training logic for the agent."""
        pass

    @abstractmethod
    def test(self):
        """The main testing/backtesting logic for the agent."""
        pass