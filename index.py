import discord, io, requests
import csv
import time
import random
from discord.ext import commands
import nest_asyncio
nest_asyncio.apply()
from collections import defaultdict

import os

# Reemplaza con tu token de bot
TOKEN = os.getenv('DISCORD_TOKEN')
prefijo = os.getenv('DISCORD_PREFIX', "!")
drive_url = os.getenv('DRIVE_URL', "")

# Define intents
intents = discord.Intents.default()  # Include all default intents
intents.members = True  # Enable member-related events (for changing nicknames)
intents.message_content = True  # Enable if your bot needs to read message content
intents.voice_states = True  # Enable monitoring of voice state events
intents.guilds = True  # Enable guild updates (required for member updates)

# Crea una instancia del bot with intents
bot = commands.Bot(command_prefix=prefijo, intents=intents)


def actualizar_datos():
    user_data = defaultdict(list)
    try:
        with open('data/apodos.csv', mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    user_id = row.get('id', '')
                    apodo = row.get('apodo', '')
                    if not user_id or not apodo:
                        continue
                    user_data[int(user_id.strip())].append(apodo.strip())
                except ValueError:
                    print(f"Error al procesar la fila: {row}")
                    continue
        print("Datos actualizados:", user_data)
        return user_data
    except Exception as e:
        print(f"Error al leer el archivo data/apodos.csv: {e}")
        return None

user_data = actualizar_datos()

def buscar_nick(user_id, anterior:str=None):
    nicks = user_data.get(user_id)
    if not nicks:
        print(f"No se encontró un apodo para el usuario con ID {user_id}")
        return None
        
    opciones = [n for n in nicks if n != anterior]
    if not opciones:
        # Si la única opción es el apodo actual, devolvemos el actual o None
        return anterior
        
    res = random.choice(opciones)
    print(f"Nuevo apodo seleccionado para {user_id}: {res}")
    return res

@bot.event
async def on_ready():
    global bot_id
    bot_id = bot.user.id
    print(f'{bot.user} se ha conectado a Discord!')

@bot.command()
async def cn(ctx, user_id: int):
    """Cambia aleatoriamente el nombre de un usuario."""
    member = ctx.guild.get_member(user_id)
    new_name = buscar_nick(user_id, member.nick)

    if new_name is not None:
        try:
            if member:
                await member.edit(nick=new_name)
                print(f"El apodo de {member.mention} ha sido cambiado a {new_name}.")
            else:
                print(f"No se encontró al usuario con ID {user_id} en el servidor.")
        except discord.Forbidden as error:
            print(f"No tengo permisos para cambiar el apodo: {error}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Cambia el nombre de usuario cuando entra a un canal de voz."""
    if before.channel is None and after.channel is not None:  # Usuario entra a un canal de voz
        new_name = buscar_nick(member.id, member.nick)
        if new_name is not None:
            try:
                await member.edit(nick=new_name)
                print(f"El nombre de {member.display_name} ha sido cambiado a {new_name}.")
            except discord.Forbidden:
                print(f"No tengo permisos para cambiar el nombre de {member.display_name}.")

@bot.command()
async def actualizar(ctx):
    global user_data
    nuevos_datos = actualizar_datos()
    if nuevos_datos:
        user_data = nuevos_datos
        await ctx.send("Datos de apodos actualizados con éxito.")
    else:
        await ctx.send("Error al actualizar los datos.")

@bot.event
async def on_member_update(before, after):
    """Detecta cuando el apodo de un usuario ha cambiado."""
    if before.nick != after.nick:
        if before.id != bot_id and not after.nick in user_data[after.id]:  # Verificamos que el cambio no lo haya hecho el bot
            print(f"El apodo de {before.display_name} ha sido cambiado de {before.nick} a {after.nick}.")
            time.sleep(13)
            new_name = buscar_nick(after.id, after.nick)
            if new_name is not None:
                try:
                    await after.edit(nick=new_name)
                    print(f"El apodo de {before.display_name} ha sido restablecido a {new_name}.")
                except discord.Forbidden:
                    print(f"No tengo permisos para cambiar el apodo de {before.display_name}.")

bot.run(TOKEN)