import asyncio
from datetime import datetime, timedelta
from racetime_bot import RaceHandler, monitor_cmd, can_monitor


class RandoHandler(RaceHandler):
    stop_at = ["cancelled", "finished"]

    STANDARD_RACE_PERMALINK = "QwEAAACAcDF8CQAAAAACAAAA"
    STANDARD_SPOILER_RACE_PERMALINK = "QwEAAACAcDF8CQAAAAACAAAA"

    def __init__(self, generator, **kwargs):
        super().__init__(**kwargs)

        self.generator = generator
        self.loop = asyncio.get_event_loop()
        self.loop_ended = False

    async def begin(self):
        self.state["permalink"] = self.STANDARD_RACE_PERMALINK
        self.state["spoiler"] = False

    async def ex_francais(self, args, message):
        self.state["use_french"] = True
        await self.send_message("Bot responses will now also be in French.")
        await self.send_message("Translate 'Bot responses will now also be in French.' to French.")

    async def ex_log(self, args, message):
        if self.state.get("spoiler_url") and self.state.get("spoiler"):
            url = self.state.get("spoiler_url")
            await self.send_message(f"Spoiler Log can be found at {url}")

    async def ex_spoiler(self, args, message):
        spoiler = not self.state.get("spoiler")
        self.state["spoiler"] = spoiler
        if spoiler:
            await self.send_message("Will create a public sharable Spoiler Log")
        else:
            await self.send_message("Will NOT create a public sharable Spoiler Log")

    async def ex_seed(self, args, message):
        if not self.state.get("permalink_available"):
            await self.send_message("There is no seed! Please use !rollseed to get one")
            if self.state.get("use_french"):
                await self.send_message(
                    "Translate 'There is no permalink! Please use !rollseed to get a permalink' to French")
            return
        permalink = self.state.get("permalink")
        hash = self.state.get("hash")
        seed = self.state.get("seed")
        await self.send_message(f"Seed: {seed}, Hash: {hash}, Permalink: {permalink}")
        if self.state.get("use_french"):
            await self.send_message(f"Translate 'The permalink is: {permalink}' to French.")

    @monitor_cmd
    async def ex_lock(self, args, message):
        self.state["locked"] = True
        await self.send_message("Seed rolling is now locked.")
        if self.state.get("use_french"):
            await self.send_message("Translate 'Seed rolling is now locked.' to French.")

    @monitor_cmd
    async def ex_unlock(self, args, message):
        self.state["locked"] = False
        await self.send_message("Seed rolling is now unlocked")
        if self.state.get("use_french"):
            await self.send_message("Translate 'Seed rolling is now locked' to French.")

    @monitor_cmd
    async def ex_reset(self, args, message):
        self.state["permalink"] = None
        self.state["seed"] = None
        self.state["hash"] = None
        self.state["permalink_available"] = False
        self.state["spoiler"] = False
        self.state["spoiler_url"] = None
        await self.send_message("The Seed has been reset.")

    async def ex_rollseed(self, args, message):
        if self.state.get("locked") and not can_monitor(message):
            await self.send_message("Seed rolling is locked! Only the creator of this room, a race monitor, "
                                    "or a moderator can roll a seed.")
            if self.state.get("use_french"):
                await self.send_message("Translate 'Seed rolling is locked! Only the creator of this room, a race "
                                        "monitor, or a moderator can roll a seed.'")
            return

        if self.state.get("permalink_available"):
            await self.send_message("The seed is already rolled! Use !seed to view it.")
            if self.state.get("use_french"):
                await self.send_message("Translate 'The seed is already rolled! Use !permalink to view it.' to French.")
            return

        await self.send_message("Rolling seed.....")
        generated_seed = self.generator.generate_seed(self.state.get("permalink"), self.state.get("spoiler"))
        permalink = generated_seed.get("permalink")
        hash = generated_seed.get("hash")
        seed = generated_seed.get("seed")
        version = generated_seed.get("version")

        self.logger.info(permalink)

        self.state["permalink"] = permalink
        self.state["hash"] = hash
        self.state["seed"] = seed
        self.state["permalink_available"] = True

        await self.send_message(f"{version} Permalink: {permalink}, Hash: {hash}")

        if self.state.get("spoiler"):
            url = generated_seed.get("url")
            self.state["spoiler_url"] = url
            await self.send_message(f"Spoiler Log URL available at {url}")

        await self.set_raceinfo(f" - {version} Seed: {seed}, Hash: {hash}, Permalink: {permalink}", False, False)
