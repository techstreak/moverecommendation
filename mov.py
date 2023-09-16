import numpy as np
import pandas as pd
import streamlit as st
import sqlite3
import json

# Load movie data
movies_df = pd.read_csv("tmdb_5000_movies.csv")

def extract_genre_names(genre_data):
    try:
        genre_list = json.loads(genre_data.replace("'", "\""))
        return [genre['name'] for genre in genre_list]
    except (json.JSONDecodeError, TypeError):
        return []

# Convert the 'genres' column to list of genre names
movies_df['genres'] = movies_df['genres'].apply(extract_genre_names)

# Connect to the SQLite database
conn = sqlite3.connect('user_history.db')
cursor = conn.cursor()

# Create a table to store user history
cursor.execute('''
   CREATE TABLE IF NOT EXISTS user_history (
        user_id TEXT,
        movie_title TEXT,
        rating REAL,
        genre TEXT,  -- Add this line to create the genre column
        PRIMARY KEY (user_id, movie_title)
    )
''')

conn.commit()

# Sample user data with user preferences
user_preferences = {
    'user1': ['Horror'],
    'user2': ['Action'],
    'user3': ['Drama', 'Comedy'],
}

# Track the current page using Session State
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

def update_user_history(user_id, movie_title, rating, genre):
    # Update the user's history in the database
    cursor.execute("INSERT OR REPLACE INTO user_history (user_id, movie_title, rating, genre) VALUES (?, ?, ?, ?)", (user_id, movie_title, rating, genre))
    conn.commit()

def get_user_history(user_id):
    # Retrieve user history from the database
    cursor.execute("SELECT movie_title FROM user_history WHERE user_id = ?", (user_id,))
    return [row[0] for row in cursor.fetchall()]

def get_movie_details(movie_title, movies_df):
    # Use case-insensitive comparison and strip extra spaces
    movie_title = movie_title.strip().lower()
    movie = movies_df[movies_df['title'].str.strip().str.lower() == movie_title]

    if movie.empty:
        return None

    genre_data = movie['genres'].values[0]
    
    if not genre_data:
        return None

    try:
        genres = extract_genre_names(genre_data)
        formatted_genres = ', '.join(genres)
    except Exception as e:
        formatted_genres = "N/A"
        st.warning(f"Error processing genres for '{movie_title}': {str(e)}")
    
    # Make sure to access columns that exist in the DataFrame
    selected_columns = ['title', 'original_language', 'popularity', 'release_date']
    movie_details = movie[selected_columns]
    movie_details['genres'] = formatted_genres
    
    return movie_details

def get_movie_details(movie_title, movies_df):
    # Use case-insensitive comparison and strip extra spaces
    movie_title = movie_title.strip().lower()
    movie = movies_df[movies_df['title'].str.strip().str.lower() == movie_title]

    if movie.empty:
        return None

    genre_data = movie['genres'].values[0]
    
    if not genre_data:
        return None

    try:
        genres = extract_genre_names(genre_data)
        formatted_genres = ', '.join(genres)
    except Exception as e:
        formatted_genres = "N/A"
        st.warning(f"Error processing genres for '{movie_title}': {str(e)}")
    
    return movie[['title', formatted_genres, 'original_language', 'popularity', 'release_date']]

# Create a Streamlit web app
st.title("Movie Recommendation System")

# User input section
user_id = st.text_input("Enter your user ID (e.g., user1, user2, user3):")

# Number of movies to display per page
movies_per_page = 10

if user_id in user_preferences:
    user_history = get_user_history(user_id)
    recommended_movies = recommend_movies_for_user(user_id, movies_df, user_preferences, user_history, st.session_state.current_page, movies_per_page)
    st.subheader(f"Top 10 Movie Recommendations for {user_id} (Preferred Genres: {', '.join(user_preferences[user_id])}):")

    # Display the table with specific columns
    selected_columns = ['title', 'genres', 'original_language', 'popularity', 'release_date']
    st.write(recommended_movies[selected_columns])

    # Ask for the selected movie from the top 10 recommendations
    selected_movie_title = st.text_input("Enter the title of the movie you want to know more about:")

    # Get and display details of the selected movie
    movie_details = get_movie_details(selected_movie_title, movies_df)
    if movie_details is not None:
        st.subheader("Movie Details:")
        st.write(movie_details)

        if selected_movie_title not in user_history:
            selected_movie_genre = movies_df[movies_df['title'] == selected_movie_title]['genres'].values[0]
            update_user_history(user_id, selected_movie_title, 1.0, selected_movie_genre)
            st.write(f"'{selected_movie_title}' has been added to your history.")
        else:
            st.warning(f"'{selected_movie_title}' is already in your history.")
    else:
        st.warning(f"Movie '{selected_movie_title}' not found in the recommendations.")

# Previous and Next buttons at the bottom
col1, col2 = st.columns(2)
if col1.button("Previous"):
    if st.session_state.current_page > 1:
        st.session_state.current_page -= 1

if col2.button("Next"):
    st.session_state.current_page += 1
