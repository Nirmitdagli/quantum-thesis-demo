"""Cloud cost calculator for the HERO framework.

Maps each tier (CPU, GPU, QPU) to representative cloud services and
their published 2026 prices. We deliberately use ON-DEMAND pricing
(no spot, no commitments) for an honest worst-case-cost estimate.

All prices verified against vendor public pricing pages, April 2026.
"""

# 2026 published cloud pricing (USD)
# Sources cited in the paper bibliography.
CLOUD_PRICING = {
    # ---------- CPU tier ----------
    "AWS_EC2_c7i.4xlarge": {
        "service": "AWS EC2 c7i.4xlarge",
        "tier":    "CPU",
        "vcpus":   16,
        "ram_gb":  32,
        "price_per_hour": 0.7140,         # USD / hr (us-east-1)
    },
    "GCP_n2_standard_16": {
        "service": "GCP n2-standard-16",
        "tier":    "CPU",
        "vcpus":   16,
        "ram_gb":  64,
        "price_per_hour": 0.7768,
    },

    # ---------- GPU tier ----------
    "AWS_g5.xlarge": {
        "service": "AWS g5.xlarge (NVIDIA A10G)",
        "tier":    "GPU",
        "gpu":     "NVIDIA A10G",
        "ram_gb":  24,
        "price_per_hour": 1.006,
    },
    "AWS_p5.48xlarge": {
        "service": "AWS p5.48xlarge (8x NVIDIA H100)",
        "tier":    "GPU",
        "gpu":     "8x NVIDIA H100",
        "ram_gb":  640,
        "price_per_hour": 98.32,
    },

    # ---------- QPU tier ----------
    "IBM_Quantum_Eagle": {
        "service": "IBM Quantum (Eagle r3, 127 qubits)",
        "tier":    "QPU",
        "qubits":  127,
        "price_per_second": 1.60,         # IBM Quantum Premium plan, per-second
    },
    "AWS_Braket_IonQ": {
        "service": "AWS Braket (IonQ Aria, 25 qubits)",
        "tier":    "QPU",
        "qubits":  25,
        "price_per_task": 0.30,           # Per task submission
        "price_per_shot": 0.03,           # Per shot
    },
    "AWS_Braket_Rigetti": {
        "service": "AWS Braket (Rigetti Ankaa, 84 qubits)",
        "tier":    "QPU",
        "qubits":  84,
        "price_per_task": 0.30,
        "price_per_shot": 0.0009,
    },
    "Azure_Quantum_Quantinuum": {
        "service": "Azure Quantum (Quantinuum H2, 56 qubits)",
        "tier":    "QPU",
        "qubits":  56,
        "price_per_minute": 12.50,        # Quantinuum H-series, on-demand
    },
}

# Default representative service per tier (used in tables and figures)
DEFAULT_SERVICE = {
    "CPU": "AWS_EC2_c7i.4xlarge",
    "GPU": "AWS_g5.xlarge",
    "QPU": "AWS_Braket_Rigetti",
}


def cost_per_task(tier: str, runtime_s: float, n_shots: int = 0) -> float:
    """Estimate cloud cost for a single task on the given tier.

    Args:
        tier: "CPU", "GPU", or "QPU"
        runtime_s: wall-clock runtime in seconds
        n_shots: only used for QPU billing (ignored otherwise)

    Returns:
        Cost in USD.
    """
    svc_key = DEFAULT_SERVICE[tier]
    svc = CLOUD_PRICING[svc_key]

    if "price_per_hour" in svc:
        return runtime_s * svc["price_per_hour"] / 3600.0
    if "price_per_second" in svc:
        return runtime_s * svc["price_per_second"]
    if "price_per_minute" in svc:
        return runtime_s * svc["price_per_minute"] / 60.0
    if "price_per_task" in svc:
        # task billing + per-shot
        return svc["price_per_task"] + svc.get("price_per_shot", 0) * n_shots
    return 0.0


def cost_per_million(tier: str, runtime_s: float, n_shots: int = 2000) -> float:
    """Cost to run 1,000,000 such tasks (more interpretable for the paper)."""
    return cost_per_task(tier, runtime_s, n_shots) * 1_000_000


def all_tiers_cost(runtime_per_tier: dict, shots: int = 2000) -> dict:
    """Compute per-task and per-million costs across all three tiers."""
    return {
        tier: {
            "service": CLOUD_PRICING[DEFAULT_SERVICE[tier]]["service"],
            "runtime_s": runtime_per_tier[tier],
            "cost_per_task_usd": cost_per_task(tier, runtime_per_tier[tier], shots),
            "cost_per_million_usd": cost_per_million(tier, runtime_per_tier[tier], shots),
        }
        for tier in ["CPU", "GPU", "QPU"]
    }


if __name__ == "__main__":
    # Demo with measured runtimes from the v6 simulation
    measured = {"CPU": 0.005, "GPU": 0.001, "QPU": 1.155}
    costs = all_tiers_cost(measured)
    print("Cloud cost per task and per million tasks (April 2026 pricing):\n")
    for tier, c in costs.items():
        print(f"  {tier} ({c['service']}):")
        print(f"    runtime/task:  {c['runtime_s']:.4f} s")
        print(f"    $/task:        ${c['cost_per_task_usd']:.6f}")
        print(f"    $/1M tasks:    ${c['cost_per_million_usd']:,.2f}")
        print()
