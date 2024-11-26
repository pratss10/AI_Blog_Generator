from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json
import os
import sys
import pytube
from moviepy import *
import requests

# import assemblyai as aai
# import openai
from groq import Groq

# Replace 'your_api_key_here' with your actual Groq API key
client = Groq(api_key='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')

from .models import BlogPost

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    yt_link=""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            yt_link = data['link']
            
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid data sent'}, status=400)


        # get yt title
        # title = yt_title(yt_link) bypasss
        # get transcript
        transcription = get_transcription(yt_link)
        print("trans:"+transcription)
        if not transcription:
            return JsonResponse({'error': " Failed to get transcript"}, status=500)


        # use OpenAI to generate the blog
        blog_content = generate_blog_from_transcription(transcription)
        if not blog_content:
            return JsonResponse({'error': " Failed to generate blog article"}, status=500)

        # save blog article to database
        new_blog_article = BlogPost.objects.create(
            user=request.user,
            youtube_title="title",
            youtube_link=yt_link,
            generated_content=blog_content,
        )
        new_blog_article.save()

        # return blog article as a response
        return JsonResponse({'content': blog_content})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

def yt_title(link):

    yt = pytube.YouTube(link)
    
    title = yt.title
    print("reactde")
    
    return title

import sys
from moviepy import *

import os
import yt_dlp
from moviepy import AudioFileClip

def download_youtube_as_mp3(youtube_link):
    try:
        # Define the output file format and location
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloaded_audio.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # Download the audio using yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_link])

        # Find the downloaded file (it should be in the current directory)
        base, ext = os.path.splitext('downloaded_audio.mp3')
        mp3_file = f"{base}.mp3"

        if not os.path.exists(mp3_file):
            print("Failed to download and convert the audio.")
            return None

        print(f"MP3 file saved as {mp3_file}")
        return mp3_file

    except Exception as e:
        print(f"An error occurred: {e}")
        return None




def get_transcription(link):
    audio_file = download_youtube_as_mp3(link)
    with open("downloaded_audio.mp3", "rb") as file:
        transcription = client.audio.transcriptions.create(
        file=("downloaded_audio.mp3", file.read()),
        model="whisper-large-v3",
        prompt="Specify context or spelling",  # Optional
        response_format="json",  # Optional
        language="en",  # Optional
        temperature=0.0  # Optional
        )
    return transcription.text




def generate_blog_from_transcription(transcription: str) -> str:
    """
    

    Args:
    transcription (str): The transcription text from a YouTube video.

    Returns:
    str: The generated blog article.
    """
    response = client.chat.completions.create(
        messages=[
                {
                    "role": "user",
                    "content": f"Generate a comprehensive blog article based on the following YouTube video transcription:\n\n{transcription}",
                }
            ],

        model="llama-3.1-70b-versatile",
        max_tokens=1000
    )

    generated_content = response.choices[0].message.content
    return generated_content


def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

def blog_details(request, pk):
    blog_article_detail = BlogPost.objects.get(id=pk)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
    else:
        return redirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password"
            return render(request, 'login.html', {'error_message': error_message})
        
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']
        
        if password == repeatPassword:
            try:
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except:
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})
        else:
            error_message = 'Password do not match'
            return render(request, 'signup.html', {'error_message':error_message})
        
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('/')
