imports_string = '''
# cc
import websocket, httpx
requests = httpx
from requests.exceptions import TooManyRedirects
from python_ghost_cursor import path
from price_parser import parse_price

# Mine
from timeout import sleep_timer, random_timeout, sleep_for
from printr import logger, print, current_time, same_line, printr
from error_alerts import telegram

# Socials
import tweepy, twitter, praw
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired, FeedbackRequired, PleaseWaitFewMinutes, ClientThrottledError, ClientError
from telethon.sync import TelegramClient
from yt_dlp import YoutubeDL

# Scraping
import requestium, feedparser
from bs4 import BeautifulSoup
from selenium_shortcuts import setup_shortcuts

# Google
import gspread
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Server
from flask import Flask, render_template, request
from waitress import serve as server
from requests_futures.sessions import FuturesSession

# Misc
import schedule, demoji
from ffprobe import FFProbe
from dateutil.parser import parse as parse_date
'''

# exec(imports_string)

# # Defaults
# import os, sys, pickle, base64, re, subprocess, json
# from threading import Thread