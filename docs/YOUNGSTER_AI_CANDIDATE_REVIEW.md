# Youngster AI candidate review

This workflow **does not generate images or call an AI provider**. It processes a PNG generated elsewhere. It never changes the in-game Youngster or commits the candidate.

1. Put a candidate PNG in `gfx/trainers/conversions/youngster_ai_input.png` on the `feature/gen2-sprite-conversions` branch.
2. Run **Review Youngster AI sprite candidate** via Actions on that branch with that path as the input.
3. Download `youngster-ai-candidate-review` containing the 56x56 draft, 5x preview comparison and JSON report.

The grayscale reduction is intentionally a **diagnostic baseline**, not a trained Gen 2 reconstruction. A visually attractive generated image is not proof of native pixel placement; the result requires human visual inspection, especially on the face, hands, pose and foot spacing. A solid background triggers a warning rather than pretending transparency was reconstructed.
