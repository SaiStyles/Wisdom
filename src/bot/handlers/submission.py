import logging
import discord
from src.db.repositories import members, predictions
from src.services.session_state import is_submission_open
from src.bot.views import ConfidenceView
from src.utils.timezones import today_et
import config

logger = logging.getLogger(__name__)

PRED_LABELS = config.PREDICTION_LABELS


async def handle_prediction(interaction: discord.Interaction, prediction: int) -> None:
    if not is_submission_open():
        await interaction.response.edit_message(content="⏰ Submissions are closed.", view=None, embed=None)
        return

    member = members.get_by_discord_id(str(interaction.user.id))
    if not member:
        await interaction.response.edit_message(content="You're not on the roster.", view=None, embed=None)
        return

    today = today_et()
    if predictions.has_submitted(member.id, today):
        await interaction.response.edit_message(content="✅ Already locked in. No changes.", view=None, embed=None)
        return

    label = PRED_LABELS[prediction]
    await interaction.response.edit_message(
        content=f"You chose: **{label}**\n\nNow pick your confidence (1 = low, 10 = high):",
        view=ConfidenceView(prediction),
        embed=None,
    )


async def handle_confidence(interaction: discord.Interaction, prediction: int, confidence: int) -> None:
    if not is_submission_open():
        await interaction.response.edit_message(content="⏰ Submissions are closed.", view=None, embed=None)
        return

    member = members.get_by_discord_id(str(interaction.user.id))
    if not member:
        await interaction.response.edit_message(content="You're not on the roster.", view=None, embed=None)
        return

    today = today_et()
    saved = predictions.save(member.id, prediction, confidence, today)

    if saved:
        label = PRED_LABELS[prediction]
        await interaction.response.edit_message(
            content=f"✅ Locked in: **{label}** — Confidence {confidence}/10\n\nSee you at 9:29 AM ET for the signal.",
            view=None,
            embed=None,
        )
        logger.info("Submission saved: member=%s pred=%s conf=%s", member.id, prediction, confidence)
    else:
        await interaction.response.edit_message(content="✅ Already locked in. No changes.", view=None, embed=None)
