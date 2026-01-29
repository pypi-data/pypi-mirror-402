import torch
import torch.nn as nn
import torch.nn.functional as F
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class DPOLoss(nn.Module):
    """
    Direct Preference Optimization (DPO) Loss implementation.

    Formula: L_DPO = -log(σ(β * log(π_θ(y_w | x) / π_ref(y_w | x)) - β * log(π_θ(y_l | x) / π_ref(y_l | x))))

    Where:
    - π_θ: policy model probabilities
    - π_ref: reference model probabilities
    - y_w: preferred (chosen) response
    - y_l: dispreferred (rejected) response
    - β: temperature parameter
    - σ: sigmoid function

    For numerical stability, we work with log probabilities directly.
    """

    def __init__(self, beta: float = 0.1, reduction: str = 'mean'):
        """
        Args:
            beta: Temperature parameter for DPO loss
            reduction: Reduction method ('mean', 'sum', or 'none')
        """
        super().__init__()
        self.beta = beta
        self.reduction = reduction

    def forward(
        self,
        log_probs_w: torch.Tensor,
        log_probs_l: torch.Tensor,
        log_probs_ref_w: torch.Tensor,
        log_probs_ref_l: torch.Tensor
    ) -> Tuple[torch.Tensor, dict]:
        """
        Compute DPO loss.

        Args:
            log_probs_w: Log probabilities of preferred responses from policy model [batch_size]
            log_probs_l: Log probabilities of dispreferred responses from policy model [batch_size]
            log_probs_ref_w: Log probabilities of preferred responses from reference model [batch_size]
            log_probs_ref_l: Log probabilities of dispreferred responses from reference model [batch_size]

        Returns:
            Tuple of (loss, metrics_dict)
        """
        # Compute log ratios for numerical stability
        # log(π_θ(y_w|x) / π_ref(y_w|x)) = log(π_θ(y_w|x)) - log(π_ref(y_w|x))
        log_ratio_w = log_probs_w - log_probs_ref_w
        log_ratio_l = log_probs_l - log_probs_ref_l

        # Compute the difference: β * (log_ratio_w - log_ratio_l)
        diff = self.beta * (log_ratio_w - log_ratio_l)

        # Apply sigmoid and take log: -log(σ(diff))
        # Using log_sigmoid for numerical stability
        loss = -F.logsigmoid(diff)

        # Apply reduction
        if self.reduction == 'mean':
            loss = loss.mean()
        elif self.reduction == 'sum':
            loss = loss.sum()
        elif self.reduction == 'none':
            pass
        else:
            raise ValueError(f"Invalid reduction: {self.reduction}")

        # Compute metrics for debugging
        metrics = {
            'dpo_loss': loss.item() if loss.numel() == 1 else loss.detach().cpu().numpy(),
            'log_ratio_w_mean': log_ratio_w.mean().item(),
            'log_ratio_l_mean': log_ratio_l.mean().item(),
            'diff_mean': diff.mean().item(),
            'sigmoid_diff_mean': torch.sigmoid(diff).mean().item(),
            'beta': self.beta
        }

        # Log metrics
        logger.debug(f"DPO Loss: {metrics['dpo_loss']}")
        logger.debug(f"Log ratio W mean: {metrics['log_ratio_w_mean']}")
        logger.debug(f"Log ratio L mean: {metrics['log_ratio_l_mean']}")

        return loss, metrics

    def compute_preferences(
        self,
        policy_model,
        ref_model,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        chosen_ids: torch.Tensor,
        rejected_ids: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Helper method to compute log probabilities from models.
        This is useful for batch processing in federated learning scenarios.

        Note: In practice, models return scalar loss (averaged over batch).
        For DPO, we need per-sample log probs. This method assumes the loss
        is computed per sample or expands the scalar to batch size.

        Args:
            policy_model: The policy model (θ)
            ref_model: The reference model
            input_ids: Input token ids [batch_size, seq_len]
            attention_mask: Attention mask [batch_size, seq_len]
            chosen_ids: Chosen response token ids [batch_size, seq_len]
            rejected_ids: Rejected response token ids [batch_size, seq_len]

        Returns:
            Tuple of (log_probs_w, log_probs_l, log_probs_ref_w, log_probs_ref_l)
        """
        batch_size = input_ids.shape[0]

        with torch.no_grad():
            # Get log probs from reference model
            ref_outputs_w = ref_model(input_ids, attention_mask=attention_mask, labels=chosen_ids)
            ref_outputs_l = ref_model(input_ids, attention_mask=attention_mask, labels=rejected_ids)

            # For simplicity, assume loss is averaged; expand to batch size
            log_probs_ref_w = -ref_outputs_w.loss * torch.ones(batch_size, device=input_ids.device)
            log_probs_ref_l = -ref_outputs_l.loss * torch.ones(batch_size, device=input_ids.device)

        # Get log probs from policy model
        policy_outputs_w = policy_model(input_ids, attention_mask=attention_mask, labels=chosen_ids)
        policy_outputs_l = policy_model(input_ids, attention_mask=attention_mask, labels=rejected_ids)

        log_probs_w = -policy_outputs_w.loss * torch.ones(batch_size, device=input_ids.device)
        log_probs_l = -policy_outputs_l.loss * torch.ones(batch_size, device=input_ids.device)

        return log_probs_w, log_probs_l, log_probs_ref_w, log_probs_ref_l