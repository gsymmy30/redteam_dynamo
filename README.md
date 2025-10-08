# RedTeam Dynamo

Red-teaming test suite for DynamoGuard financial advice guardrails.

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd redteam_dynamo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure API credentials:
```bash
cp config.py.example config.py
# Edit config.py and add your DYNAMO_API_KEY
```

4. Run initial tests:
```bash
python run_tests.py
```

5. Generate report:
```bash
python generate_report.py
```

## File Structure

- `prompts.json` - Test case library with categories and attack techniques
- `run_tests.py` - Main test runner that calls DynamoGuard API
- `generate_report.py` - Generates summary reports from results
- `results/` - Directory containing timestamped test results (JSON files)
- `config.py` - API configuration (not committed)

## Attack Categories & Tactics

Based on comprehensive research into prompt injection and jailbreaking techniques:

### Categories

- **direct_injection** - Direct requests for financial advice
- **jailbreak_persona** - DAN attacks, roleplay, persona switching
- **jailbreak_framing** - Perspective shifts, hypothetical scenarios, creative writing
- **instruction_override** - "Ignore previous instructions", system rule changes, fake conversations
- **obfuscation** - Leetspeak, Base64, Unicode, URL encoding
- **structured_injection** - XML/JSON config mimicry, HTML comments, markdown attacks
- **context_manipulation** - Few-shot conditioning, context flooding
- **persuasive_tactics** - Authority endorsement, logical appeals, emotional manipulation
- **benign** - Control tests (should NOT block)

### Tactics

Over 50+ specific tactics tested including:
- `direct_override` - Straightforward financial advice requests
- `dan_attacks` - "Do Anything Now" persona adoption
- `roleplaying` - Adopting expert personas
- `perspective_shifts` - Educational/hypothetical framing
- `ignore_previous_instructions` - Explicit instruction override
- `base64_encoded_instruction` - Encoding to evade filters
- `unicode_homoglyph_swap` - Visually similar character substitution
- `policy_puppetry` - Mimicking system configuration files
- `html_comment_injection` - Hidden instructions in markup
- `few_shot_conditioning` - Learning from examples
- `authority_endorsement_persuasive` - Citing experts to justify requests
- And many more...

## Prompt Categories

Based on research from "Bullet-Proofing FinTech LLMs: 360° Red-Team Playbook":

- **direct_injection** - Explicit override attempts
- **policy_puppetry** - XML/JSON system config mimicry (CRITICAL)
- **obfuscation** - Base64/leetspeak/homoglyphs
- **hypothetical_framing** - What-if scenarios
- **persona_switching** - Roleplay attacks
- **jailbreak_creative** - Story/fiction framing
- **multi_turn_escalation** - Gradual conversation drift
- **few_shot_conditioning** - Learning from examples
- **benign** - Control tests (should NOT block)

## KPIs

- **Refusal Rate**: % of prohibited prompts correctly blocked
- **False Positive Rate**: % of benign prompts incorrectly blocked
- **Bypass Rate by Category**: Identifies weakest guardrail areas

## Adding New Test Cases

Edit `prompts.json` and add entries:

```json
{
  "id": "new_test_1",
  "category": "direct_injection",
  "subcategory": "stock_advice",
  "attack_technique": "none",
  "prompt": "Your test prompt here",
  "expected_block": true,
  "risk_level": "high"
}
```

Then run `python run_tests.py` to test new prompts.