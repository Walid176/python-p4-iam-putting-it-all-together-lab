#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # Create new user
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            
            # Set password (this will hash it)
            password = data.get('password')
            if password:
                user.password_hash = password
            
            # Save to database
            db.session.add(user)
            db.session.commit()
            
            # Store user_id in session
            session['user_id'] = user.id
            
            # Return user data
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 201
            
        except ValueError as e:
            # Handle validation errors
            return {'error': str(e)}, 422
            
        except IntegrityError as e:
            db.session.rollback()
            # Handle database constraint errors (e.g., duplicate username)
            return {'error': 'Username already exists'}, 422
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if user_id:
            user = User.query.filter(User.id == user_id).first()
            
            if user:
                return {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }, 200
        
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Find user by username
        user = User.query.filter(User.username == username).first()
        
        # Authenticate user
        if user and user.authenticate(password):
            # Store user_id in session
            session['user_id'] = user.id
            
            # Return user data
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 200
        
        return {'error': 'Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        
        if user_id:
            # Remove user_id from session
            session.pop('user_id', None)
            return '', 204
        
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        # Get all recipes
        recipes = Recipe.query.all()
        
        # Format response with nested user data
        recipes_data = []
        for recipe in recipes:
            recipes_data.append({
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username,
                    'image_url': recipe.user.image_url,
                    'bio': recipe.user.bio
                } if recipe.user else None
            })
        
        return recipes_data, 200
    
    def post(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Unauthorized'}, 401
        
        try:
            data = request.get_json()
            
            # Create new recipe
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            
            # Save to database
            db.session.add(recipe)
            db.session.commit()
            
            # Get the user for nested response
            user = User.query.get(user_id)
            
            # Return recipe data with nested user
            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'image_url': user.image_url,
                    'bio': user.bio
                }
            }, 201
            
        except ValueError as e:
            # Handle validation errors
            return {'error': str(e)}, 422
            
        except IntegrityError as e:
            db.session.rollback()
            return {'error': 'Failed to create recipe'}, 422
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)