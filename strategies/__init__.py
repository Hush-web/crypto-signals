"""
strategies/ — Drop-in custom strategies.

Each strategy is a function that takes an indicator-enriched DataFrame
(see signals.add_indicators) and returns a dict:
    {"action": "BUY"|"SELL"|"HOLD", "confidence": "HIGH"|"MEDIUM"|"LOW", "reason": str}

See strategies/example_strategy.py for a template, and README.md for how
to wire a new strategy into signals.generate_signal().
"""
