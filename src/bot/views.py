import discord
import config


class PredictionView(discord.ui.View):
    """Persistent view — survives bot restarts. Shown in the daily DM."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📈 Expansion Up", custom_id="pred:1", style=discord.ButtonStyle.primary)
    async def pred_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.submission import handle_prediction
        await handle_prediction(interaction, 1)

    @discord.ui.button(label="📉 Expansion Down", custom_id="pred:2", style=discord.ButtonStyle.primary)
    async def pred_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.submission import handle_prediction
        await handle_prediction(interaction, 2)

    @discord.ui.button(label="↔️ Expansion Both", custom_id="pred:3", style=discord.ButtonStyle.primary)
    async def pred_both(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.submission import handle_prediction
        await handle_prediction(interaction, 3)

    @discord.ui.button(label="⬜ Range", custom_id="pred:4", style=discord.ButtonStyle.primary)
    async def pred_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.submission import handle_prediction
        await handle_prediction(interaction, 4)


class ConfidenceView(discord.ui.View):
    """Non-persistent — built per prediction, short-lived."""

    def __init__(self, prediction: int):
        super().__init__(timeout=600)
        self.prediction = prediction
        for i in range(1, 11):
            btn = discord.ui.Button(
                label=str(i),
                custom_id=f"conf:{prediction}:{i}",
                style=discord.ButtonStyle.secondary,
                row=0 if i <= 5 else 1,
            )
            btn.callback = self._make_callback(i)
            self.add_item(btn)

    def _make_callback(self, confidence: int):
        async def cb(interaction: discord.Interaction):
            from src.bot.handlers.submission import handle_confidence
            await handle_confidence(interaction, self.prediction, confidence)
        return cb


class ResultView(discord.ui.View):
    """Persistent — admin taps after session to record actual outcome."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📈 Expansion Up", custom_id="result:1", style=discord.ButtonStyle.success)
    async def res_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.admin import handle_result
        await handle_result(interaction, 1)

    @discord.ui.button(label="📉 Expansion Down", custom_id="result:2", style=discord.ButtonStyle.success)
    async def res_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.admin import handle_result
        await handle_result(interaction, 2)

    @discord.ui.button(label="↔️ Expansion Both", custom_id="result:3", style=discord.ButtonStyle.success)
    async def res_both(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.admin import handle_result
        await handle_result(interaction, 3)

    @discord.ui.button(label="⬜ Range", custom_id="result:4", style=discord.ButtonStyle.success)
    async def res_range(self, interaction: discord.Interaction, button: discord.ui.Button):
        from src.bot.handlers.admin import handle_result
        await handle_result(interaction, 4)
