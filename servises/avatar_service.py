import random
import string

from typing import Optional
from PIL import Image, ImageDraw
from fastapi import UploadFile

import io
import base64
import os

from pathlib import Path


class AvatarService:
    def __init__(self):
        self.avatar_size = 64
        self.avatars_dir = Path("static/avatars")
        self.avatars_dir.mkdir(parents=True, exist_ok=True)
        
        self.colors = [
            "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
            "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
            "#F8C471", "#82E0AA", "#F1948A", "#85C1E9", "#D7BDE2"
        ]
    
    async def upload_avatar(self, file: UploadFile, user_id: str) -> str:
        try:
            if not file.content_type.startswith('image/'):
                raise ValueError("File must be an image")
            
            contents = await file.read()
            
            img = Image.open(io.BytesIO(contents))
            
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img = img.resize((self.avatar_size, self.avatar_size), Image.Resampling.LANCZOS)
            
            file_extension = file.filename.split('.')[-1] if file.filename else 'png'
            filename = f"avatar_{user_id}_{random.randint(1000, 9999)}.{file_extension}"
            filepath = self.avatars_dir / filename
            
            img.save(filepath, 'PNG')
            
            return f"/static/avatars/{filename}"
            
        except Exception as e:
            print(f"Error uploading avatar: {e}")
            raise ValueError(f"Failed to upload avatar: {str(e)}")
    
    def get_avatar_info(self) -> dict:
        return {
            "avatar_url": self._get_default_avatar_url(),
            "avatar_size": self.avatar_size,
            "supported_formats": ["png", "jpg", "jpeg", "gif", "webp"],
            "max_file_size": 5 * 1024 * 1024  # 5MB
        }
    
    def generate_random_avatar(self, user_id: str) -> str:
        try:
            img = Image.new('RGB', (self.avatar_size, self.avatar_size), color='white')
            draw = ImageDraw.Draw(img)
            
            random.seed(hash(user_id))
            
            bg_color = random.choice(self.colors)
            draw.rectangle([0, 0, self.avatar_size, self.avatar_size], fill=bg_color)
            
            num_shapes = random.randint(3, 6)
            
            for _ in range(num_shapes):
                shape_type = random.choice(['circle', 'rectangle', 'triangle'])
                color = random.choice(self.colors)
                
                if shape_type == 'circle':
                    x = random.randint(10, self.avatar_size - 10)
                    y = random.randint(10, self.avatar_size - 10)
                    radius = random.randint(5, 15)
                    draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
                
                elif shape_type == 'rectangle':
                    x1 = random.randint(5, self.avatar_size - 20)
                    y1 = random.randint(5, self.avatar_size - 20)
                    x2 = x1 + random.randint(10, 20)
                    y2 = y1 + random.randint(10, 20)
                    draw.rectangle([x1, y1, x2, y2], fill=color)
                
                elif shape_type == 'triangle':
                    points = []
                    for _ in range(3):
                        x = random.randint(5, self.avatar_size - 5)
                        y = random.randint(5, self.avatar_size - 5)
                        points.append((x, y))
                    draw.polygon(points, fill=color)
            
            if len(user_id) >= 2:
                initials = user_id[:2].upper()
                text_color = 'white' if self._is_dark_color(bg_color) else 'black'
                try:
                    from PIL import ImageFont
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
                except:
                    font = ImageFont.load_default()
                
                bbox = draw.textbbox((0, 0), initials, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (self.avatar_size - text_width) // 2
                y = (self.avatar_size - text_height) // 2
                
                draw.text((x, y), initials, fill=text_color, font=font)
            
            filename = f"avatar_{user_id}_{random.randint(1000, 9999)}.png"
            filepath = self.avatars_dir / filename
            
            img.save(filepath, 'PNG')
            
            return f"/static/avatars/{filename}"
            
        except Exception as e:
            print(f"Error generating avatar: {e}")

            return self._get_default_avatar_url()
    
    def _is_dark_color(self, hex_color: str) -> bool:
        hex_color = hex_color.lstrip('#')
        
        r = int(hex_color[:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:], 16)
        
        brightness = (r * 299 + g * 587 + b * 114) / 1000
        
        return brightness < 128
    
    def _get_default_avatar_url(self) -> str:
        return "/static/avatars/default_avatar.png"
    
    def delete_avatar(self, avatar_url: str) -> bool:
        try:
            if avatar_url and avatar_url.startswith("/static/avatars/"):
                filename = avatar_url.split("/")[-1]
                filepath = self.avatars_dir / filename
                
                if filepath.exists() and filename != "default_avatar.png":
                    filepath.unlink()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting avatar: {e}")
            return False
    
    def get_avatar_size(self) -> int:
        return self.avatar_size


avatar_service = AvatarService()
