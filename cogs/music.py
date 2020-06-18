import discord
from discord.ext import commands
from discord.utils import get

import youtube_dl
import requests
import asyncio
import time

class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.song_queue = []
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    def parse_duration(self, duration):
        result = []
        seconds = duration%60
        minutes = duration//60
        hour = minutes//60
        day = hour//24

    def parse_duration(self, duration):
        result, suffix = [], ['s', 'min', 'h', 'j']
        seconds = duration%60
        minutes = duration//60
        hour = minutes//60
        day = hour//24

        for y, x in zip([x for x in [seconds, minutes, hour, day] if x != 0], suffix):
            result.append(str(y) + x)
        return "".join(result)

    def search(self, ctx, arg):
        ydl_opts = {'format': 'bestaudio', 'noplaylist':'True'}
        try:
            temp = "".join(arg[:])
            response = requests.get(temp)
        except:
            arg = " ".join(arg[:])
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)
                title = info['entries'][0]['title']
                url = info['entries'][0]['webpage_url']
                source = info['entries'][0]['formats'][0]['url']
                uploader = info['entries'][0]['uploader']
                uploader_url = info['entries'][0]['channel_url']
                duration = self.parse_duration(info['entries'][0]['duration'])
                thumbnail = info['entries'][0]['thumbnail']
        else:
            arg = "".join(arg[:])
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(arg, download=False)
                title = info['title']
                url = info['webpage_url']
                source = info['formats'][0]['url']
                uploader = info['uploader']
                uploader_url = info['channel_url']
                duration = self.parse_duration(info['duration'])
                thumbnail = info['thumbnail']

        embed = (discord.Embed(title='Tocando agora :', description=f'{title}', color=discord.Color.blue())
                 .add_field(name='Duração', value=duration)
                 .add_field(name='Pedida por:', value=ctx.message.author.display_name)
                 .add_field(name='Uploader', value=f'[{uploader}]({uploader_url})')
                 .add_field(name='URL', value=f'[link para o vídeo]({url})')
                 .set_thumbnail(url=thumbnail))

        return {'embed': embed, 'source': source, 'title': title}

    @commands.command(aliases=['p'], brief='!play [url/key-word]', description='Plays the desired song')
    async def play(self, ctx, *arg):
        channel = ctx.message.author.voice.channel
        if not channel:
            await ctx.send("Você não esta em nenhum canal!")
        else:
            voice = get(self.bot.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await ctx.send(f':Ayres entrou em **{channel}**')
                voice = await channel.connect()

            def play_next(ctx):
                del self.song_queue[0]
                if len(self.song_queue) >= 1:
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    voice.play(discord.FFmpegPCMAudio(self.song_queue[0]['source'], **self.FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
                    asyncio.run_coroutine_threadsafe(ctx.send(embed=self.song_queue[0]['embed']), self.bot.loop).result()
                else:
                    time.sleep(90)
                    voice = get(self.bot.voice_clients, guild=ctx.guild)
                    if not voice.is_playing():
                        asyncio.run_coroutine_threadsafe(self.leave(ctx), self.bot.loop).result()

            song = self.search(ctx, arg)
            if not voice.is_playing():
                self.song_queue.append(song)
                voice.play(discord.FFmpegPCMAudio(song['source'], **self.FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
                await ctx.send(embed=song['embed'])
                voice.is_playing()
            else:
                self.song_queue.append(song)
                await ctx.send(f":white_check_mark: **{song['title']}** entrou para fila, ({len(self.song_queue)-1}) restantes")

    @commands.command(aliases=['q','fila','f'], brief="!queue", description="Returns the current queue")
    async def queue(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        embed = discord.Embed(color=discord.Color.blue(), title="Fila :")
        if voice and voice.is_playing():
            for i in self.song_queue:
                if self.song_queue.index(i) == 0:
                    embed.add_field(name=f'**🔴 Tocando agora :**', value=f"{i['title']}", inline=False)
                else:
                    embed.add_field(
                        name=f'**🎵 Música n°{self.song_queue.index(i)} :**', value=f"{i['title']}", inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Não estou tocando nada !")

    @commands.command(brief='!pause', description='Plays or resumes the current song')
    async def pause(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            if voice.is_playing():
                await ctx.send('⏸️ Pausada')
                voice.pause()
            else:
                await ctx.send('⏯️ Voltou')
                voice.resume()
        else:
            await ctx.send("❌ Não estou em nenhum canal !")

    @commands.command(aliases=['s', 'pass'], brief='!skip', description='Skips the current song')
    async def skip(self, ctx):
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_playing():
            await ctx.send('⏭️ Pulada')
            voice.stop()
        else:
            await ctx.send("❌ Não estou tocando nada !")

    @commands.command(aliases=['l'], brief='!leave', description="Disconnects the bot from it's channel")
    async def leave(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            self.song_queue = []
            await ctx.send(f'Ayres saiu de **{channel}**')
            await voice.disconnect()
        else:
            await ctx.send("❌ Não estou em nenhum canal !")

def setup(bot):
    bot.add_cog(Music(bot))
