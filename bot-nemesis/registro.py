import discord
from discord.ext import commands, tasks
import json

CAMINHO_USUARIOS = "usuarios.json"
ID_CANAL_REGISTRO = 1419435467903991838  # Canal 🔔┃solicitar-set
ID_CANAL_LOGS = 1419435467903991840      # <- coloque aqui o ID do canal de logs
usuarios = {}

def salvar_em_arquivo(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

class FormularioRegistro(discord.ui.Modal, title="Registro de Identidade"):
    nome = discord.ui.TextInput(label="Nome", placeholder="Digite seu nome")
    sobrenome = discord.ui.TextInput(label="Sobrenome", placeholder="Digite seu sobrenome")
    passaporte = discord.ui.TextInput(label="Passaporte", placeholder="Digite seu número de passaporte")

    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        novo_nick = f"{self.nome.value} {self.sobrenome.value} | {self.passaporte.value}"
        try:
            await interaction.user.edit(nick=novo_nick)

            usuarios[str(interaction.user.id)] = {
                "nome": self.nome.value,
                "sobrenome": self.sobrenome.value,
                "passaporte": self.passaporte.value
            }
            salvar_em_arquivo(CAMINHO_USUARIOS, usuarios)

            role_policia = discord.utils.get(interaction.guild.roles, name="Recruta")
            role_visitante = discord.utils.get(interaction.guild.roles, name="visitante")

            # Remove visitante antes
            if role_visitante and role_visitante in interaction.user.roles:
                await interaction.user.remove_roles(role_visitante)

            # Adiciona polícia
            if role_policia:
                await interaction.user.add_roles(role_policia)

            # Embed para feedback ao usuário
            embed_final = discord.Embed(
                title="**REGISTRO COMPLETO!**",
                description="*Seja bem-vindo(a) a Nemesis*",
                color=0x2ecc71  # verde sucesso
            )
            embed_final.add_field(name="👤 Nome alterado para:", value=novo_nick, inline=True)
            embed_final.add_field(name="🛂 Passaporte:", value=self.passaporte.value, inline=False)

            # Embed para logs
            embed_logs = discord.Embed(
                title="📋 Novo Registro Realizado",
                color=0x3498db  # azul
            )
            embed_logs.add_field(name="👤 Usuário:", value=interaction.user.mention, inline=True)
            embed_logs.add_field(name="🔖 Novo Nick:", value=novo_nick, inline=True)
            embed_logs.add_field(name="🛂 Passaporte:", value=self.passaporte.value, inline=False)
            embed_logs.set_footer(text=f"ID do usuário: {interaction.user.id}")

            # Envia no canal de logs
            canal_logs_registro = self.bot.get_channel(1423335327191273502)
            if canal_logs_registro:
                await canal_logs_registro.send(embed=embed_logs)

            # Feedback privado ao usuário
            await interaction.response.send_message(embed=embed_final, ephemeral=True)

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não consegui mudar seu nome ou atribuir cargos. Verifique minhas permissões.",
                ephemeral=True
            )

class BotaoRegistro(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="REGISTRAR-SE", style=discord.ButtonStyle.gray, custom_id="botao_registro")
    async def iniciar_registro(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FormularioRegistro(self.bot)
        await interaction.response.send_modal(modal)

class Registro(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.enviar_mensagem_inicial.start()

    @tasks.loop(count=1)
    async def enviar_mensagem_inicial(self):
        await self.bot.wait_until_ready()
        canal = self.bot.get_channel(ID_CANAL_REGISTRO)
        if canal:
            async for msg in canal.history(limit=10):
                if msg.author == self.bot.user and msg.components:
                    return  
            view = BotaoRegistro(self.bot)
            embed = discord.Embed(
                title="> REGISTRO - Nêmesis",
                description="Seja muito bem-vindo(a) a **Nêmesis**. A partir deste momento, solicitamos que realize o registro em nosso sistema. Para iniciar, por favor, clique no botão **REGISTRAR-SE**.",
                color=discord.Color.yellow()
            )      
            embed.set_image(url="https://cdn.discordapp.com/attachments/1419425640385482794/1421654090752065677/image.png")
            await canal.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Registro(bot))
