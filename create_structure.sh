#!/bin/bash

echo "📁 Creating project structure..."

# Root files
touch main.py db.py config.py

# Create directories
mkdir -p ui models ml assets/images

# UI files
touch ui/login.py
touch ui/register.py
touch ui/dashboard.py
touch ui/booking.py
touch ui/seats.py

# Model files
touch models/user.py
touch models/movie.py
touch models/booking.py

# ML file
touch ml/recommendation.py

echo "✅ Project structure created successfully!"