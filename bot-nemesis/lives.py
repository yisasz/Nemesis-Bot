import aiohttp
import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import json
import os

CAMINHO_LIVES = "lives_registradas.json"
OWNER_ID = 683772279854858258
CANAL_LIVES_ID = 1419439111483293857
CANAL_SET_LIVES = 1419439030936010771  # Canal 🎥・set lives-pm

def carregar_arquivo(caminho):
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def salvar_em_arquivo(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

lives_registradas = carregar_arquivo(CAMINHO_LIVES)

class Lives(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrolive", description="Registra uma nova live no sistema.")
    async def registrolive(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_SET_LIVES:
            embed = discord.Embed(
                title="Acesso Negado",
                description="Você deve usar este comando no canal autorizado para registro de lives.",
                color=discord.Color.red()
            )
            embed.set_footer(text="Verifique o canal e tente novamente.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed_nome = discord.Embed(
            title="📺 Registro de Live",
            description="Digite abaixo o **nome da live** que deseja registrar.",
            color=discord.Colour.blue()
        )
        embed_nome.set_footer(text="Etapa 1 de 2 • Nome da Live")
        embed_nome.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2989/2989988.png")
        await interaction.response.send_message(embed=embed_nome, ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg_nome = await self.bot.wait_for("message", timeout=30.0, check=check)
            nome_live = msg_nome.content.strip()

            if nome_live in lives_registradas:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="⚠️ Live já Registrada",
                        description="Essa live já foi registrada anteriormente no sistema.",
                        color=discord.Color.orange()
                    ),
                    ephemeral=True
                )
                return

            await interaction.followup.send("🔗 Agora digite o **link da live**:", ephemeral=True)
            msg_link = await self.bot.wait_for("message", timeout=30.0, check=check)
            link_live = msg_link.content.strip()

            lives_registradas[nome_live] = {
                "autor": interaction.user.display_name,
                "link": link_live
            }

            salvar_em_arquivo(CAMINHO_LIVES, lives_registradas)

            embed = discord.Embed(
                title="🎥 Live Registrada com Sucesso!",
                color=discord.Color.green()
            )
            embed.add_field(name="📝 Nome da Live", value=nome_live, inline=False)
            embed.add_field(name="🔗 Link da Live", value=link_live, inline=False)
            embed.set_footer(text="Registro finalizado com êxito.")
            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏰ Tempo Esgotado",
                    description="Você demorou demais para responder. Refaça o processo usando o comando novamente.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )

    @app_commands.command(name="excluirlive", description="Exclui uma live registrada.")
    async def excluirlive(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_SET_LIVES:
            await interaction.response.send_message("❌ Use este comando apenas no canal correto.", ephemeral=True)
            return

        await interaction.response.send_message("🗑️ Digite o **nome da live** que deseja excluir:")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg = await self.bot.wait_for("message", timeout=30.0, check=check)
            nome_live = msg.content.strip()

            autor_live = lives_registradas.get(nome_live, {}).get("autor", "")
            if nome_live in lives_registradas and (autor_live == interaction.user.display_name or interaction.user.id == OWNER_ID):
                del lives_registradas[nome_live]
                salvar_em_arquivo(CAMINHO_LIVES, lives_registradas)
                embed = discord.Embed(
                    title="🗑️ Live Excluída",
                    description=f"A live **{nome_live}** foi removida com sucesso.",
                    color=discord.Color.red()
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Ação Negada",
                        description="Live não encontrada ou você não tem permissão para excluí-la.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏰ Tempo Esgotado",
                    description="Você demorou demais para responder. Refaça o processo usando o comando novamente.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )

    @app_commands.command(name="editarlive", description="Edita nome e link de uma live.")
    async def editarlive(self, interaction: discord.Interaction):
        if interaction.channel.id != CANAL_SET_LIVES:
            await interaction.response.send_message("❌ Use este comando apenas no canal correto.", ephemeral=True)
            return

        await interaction.response.send_message("✏️ Digite o **nome da live** que deseja editar:", ephemeral=True)

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            msg_nome = await self.bot.wait_for("message", timeout=30.0, check=check)
            nome_live = msg_nome.content.strip()

            if nome_live not in lives_registradas:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="❌ Live Não Encontrada",
                        description="Não localizamos nenhuma live com esse nome.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            autor = lives_registradas[nome_live]["autor"]
            if autor != interaction.user.display_name and interaction.user.id != OWNER_ID:
                await interaction.followup.send(
                    embed=discord.Embed(
                        title="🔒 Permissão Negada",
                        description="Você não tem permissão para editar essa live.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return

            await interaction.followup.send("📝 Digite o **novo nome** para a live:", ephemeral=True)
            msg_novo_nome = await self.bot.wait_for("message", timeout=30.0, check=check)
            novo_nome = msg_novo_nome.content.strip()

            await interaction.followup.send("🔗 Agora digite o **novo link** da live:", ephemeral=True)
            msg_novo_link = await self.bot.wait_for("message", timeout=30.0, check=check)
            novo_link = msg_novo_link.content.strip()

            lives_registradas[novo_nome] = lives_registradas.pop(nome_live)
            lives_registradas[novo_nome]["link"] = novo_link
            salvar_em_arquivo(CAMINHO_LIVES, lives_registradas)

            embed = discord.Embed(
                title="✏️ Live Atualizada",
                color=discord.Color.green()
            )
            embed.add_field(name="📝 Novo Nome", value=novo_nome, inline=False)
            embed.add_field(name="🔗 Novo Link", value=novo_link, inline=False)
            embed.set_footer(text="Alteração registrada com sucesso.")
            await interaction.followup.send(embed=embed)

        except asyncio.TimeoutError:
            await interaction.followup.send(
                embed=discord.Embed(
                    title="⏰ Tempo Esgotado",
                    description="Você demorou demais para responder. Refaça o processo usando o comando novamente.",
                    color=discord.Color.orange()
                ),
                ephemeral=True
            )

# ======= TWITCH & YOUTUBE =======

async def get_twitch_app_token(client_id, client_secret):
    url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    async with aiohttp.ClientSession() as session:
        async with session.post(url) as resp:
            data = await resp.json()
            return data.get("access_token")

def extrair_canal_twitch(link):
    partes = link.split("twitch.tv/")
    return partes[1].split("/")[0] if len(partes) > 1 else None

async def verificar_live_twitch(session, token, client_id, canal):
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {token}"
    }
    url = f"https://api.twitch.tv/helix/streams?user_login={canal}"
    async with session.get(url, headers=headers) as resp:
        data = await resp.json()
        return bool(data.get("data"))

async def verificar_live_youtube(session, link):
    try:
        async with session.get(link) as resp:
            html = await resp.text()
            return "isLiveNow" in html or "LIVE_NOW" in html
    except Exception as e:
        print(f"Erro ao verificar live YouTube: {e}")
        return False

# ======= ATUALIZAÇÃO AUTOMÁTICA =======

@tasks.loop(seconds=180)
async def atualizar_lives():
    bot = atualizar_lives.bot_reference

    try:
        canal = await bot.fetch_channel(CANAL_LIVES_ID)
    except discord.NotFound:
        print("❌ Canal 🎥・lives-pm não encontrado.")
        return
    except discord.Forbidden:
        print("❌ Sem permissão para acessar o canal 🎥・lives-pm.")
        return
    except discord.HTTPException as e:
        print(f"❌ Erro ao buscar o canal: {e}")
        return

    # limpa mensagens antigas do próprio bot
    async for msg in canal.history(limit=10):
        if msg.author == bot.user:
            await msg.delete()
            await asyncio.sleep(1)

    ordem_patentes = {
        "Coronel": 1, "Tenente Coronel": 2, "Major": 3, "Capitão": 4,
        "1 Tenente": 5, "2 Tenente": 6, "Aspirante a Tenente": 7,
        "Sub Tenente": 8, "1 Sargento": 9, "1 SGT": 9,
        "2 Sargento": 10, "2 SGT": 10, "3 Sargento": 11, "3 SGT": 11,
        "Cabo": 12, "Soldado": 13, "1SD": 13, "Aluno": 14, "Aluna": 14, "2SD": 14
    }

    def get_ordem_por_patente(nome):
        for patente, ordem in ordem_patentes.items():
            if patente.lower() in nome.lower():
                return ordem
        return 99

    CLIENT_ID = "u2apxuhwnd16i131alk52iches1dxh"
    CLIENT_SECRET = "5abcdw7aenxkhm0j9vjj56jwg76dvv"

    lives_ativas = []

    async with aiohttp.ClientSession() as session:
        # pega token Twitch (a função já abre sua própria session internamente)
        access_token = await get_twitch_app_token(CLIENT_ID, CLIENT_SECRET)

        lives_ordenadas = sorted(lives_registradas.items(), key=lambda item: get_ordem_por_patente(item[0]))

        for nome, dados in lives_ordenadas:
            link = dados.get("link", "").strip()
            if not link:
                continue

            online = False

            # Verifica plataforma para usar a função correta de checagem.
            # NÃO usamos isso para formatar o embed — apenas para confirmar se está online.
            if "twitch.tv" in link:
                canal_twitch = extrair_canal_twitch(link)
                if canal_twitch:
                    try:
                        online = await verificar_live_twitch(session, access_token, CLIENT_ID, canal_twitch)
                    except Exception as e:
                        print(f"Erro verificando Twitch ({link}): {e}")
                        online = False
            elif "youtube.com" in link or "youtu.be" in link:
                try:
                    online = await verificar_live_youtube(session, link)
                except Exception as e:
                    print(f"Erro verificando YouTube ({link}): {e}")
                    online = False
            else:
                # se for outro tipo de link, pula (ou implemente verificação própria)
                continue

            if online:
                lives_ativas.append(f"{nome}\n <:Twitch:1416469235818827876> • {link}")

    # Se houver pelo menos uma live ativa, manda um único embed organizado
    if lives_ativas:
        descricao = "\n\n".join(lives_ativas)
        # evita ultrapassar limite do Discord (segurança)
        if len(descricao) > 4000:
            descricao = descricao[:3990] + "\n\n... (lista truncada)"

        embed = discord.Embed(
            title="<a:seta_verde:1395450654671241349> CANAIS AO VIVO ",
            description=descricao,
            color=discord.Color.green()
        )
        # thumbnail genérica (remove caso não queira)
        await canal.send(embed=embed)



# ======= SETUP =======

async def setup(bot):
    await bot.add_cog(Lives(bot))
    atualizar_lives.bot_reference = bot
    if not atualizar_lives.is_running():
        atualizar_lives.start()