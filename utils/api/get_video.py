from utils.db_utils.movie_db import MovieDatabase
from utils.db_utils.show_db import ShowDatabase
from fastapi import HTTPException
from typing import Dict, Any, Optional

async def get_video_details(
    content_id: str,
    media_type: str,
    quality_index: int = 0,
    season_number: Optional[int] = None,
    episode_number: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retrieve video file details for streaming based on content type and quality preferences.
    
    Args:
        content_id: ID of the movie or show
        media_type: 'movie' or 'show'
        quality_index: Index of the quality option to select (default: 0)
        season_number: Season number (required for shows)
        episode_number: Episode number (required for shows)
        
    Returns:
        Dictionary with video file details including msg_id, chat_id, and hash
    """
    try:
        if media_type == "movie":
            return await _get_movie_file_details(content_id, quality_index)
        elif media_type == "show":
            if season_number is None or episode_number is None:
                raise HTTPException(
                    status_code=400, 
                    detail="Season number and episode number are required for shows"
                )
            return await _get_show_file_details(content_id, quality_index, season_number, episode_number)
        else:
            raise HTTPException(
                status_code=400, 
                detail="Media type must be 'movie' or 'show'"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving video: {str(e)}")

async def _get_movie_file_details(movie_id: str, quality_index: int) -> Dict[str, Any]:
    """Get file details for a movie."""
    db = MovieDatabase()
    movie = db.find_movie_by_id(int(movie_id))
    
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with ID {movie_id} not found")
    
    if "quality" not in movie or not movie["quality"]:
        raise HTTPException(status_code=404, detail=f"No quality options available for movie {movie_id}")
    
    
    if quality_index < 0 or quality_index >= len(movie["quality"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid quality index. Available range: 0-{len(movie['quality'])-1}"
        )
    
    selected_quality = movie["quality"][quality_index]
    file_hash = selected_quality.get("file_hash")
    
    if not file_hash:
        raise HTTPException(status_code=404, detail="File ID not found for selected quality")
    
    msg_id = selected_quality.get("msg_id")
    chat_id = selected_quality.get("chat_id")
    
    return {
        "msg_id": msg_id,
        "chat_id": chat_id,
        "hash": file_hash
    }

async def _get_show_file_details(
    show_id: str, 
    quality_index: int, 
    season_number: int, 
    episode_number: int
) -> Dict[str, Any]:
    """Get file details for a TV show episode."""
    db = ShowDatabase()
    show = db.find_show_by_id(int(show_id))
    
    if not show:
        raise HTTPException(status_code=404, detail=f"Show with ID {show_id} not found")
    
    
    season = next((s for s in show.get("season", []) if s["season_number"] == season_number), None)
    if not season:
        raise HTTPException(status_code=404, detail=f"Season {season_number} not found")
    
    
    episode = next((e for e in season.get("episodes", []) if e["episode_number"] == episode_number), None)
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {episode_number} not found in season {season_number}")
    
    
    if "quality" not in episode or not episode["quality"]:
        raise HTTPException(status_code=404, detail=f"No quality options available for episode")
    
    
    if quality_index < 0 or quality_index >= len(episode["quality"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid quality index. Available range: 0-{len(episode['quality'])-1}"
        )
    
    selected_quality = episode["quality"][quality_index]
    file_hash = selected_quality.get("file_hash")
    
    if not file_hash:
        raise HTTPException(status_code=404, detail="File ID not found for selected quality")
    
    msg_id = selected_quality.get("msg_id")
    if not msg_id:
        raise HTTPException(status_code=404, detail="Message ID not found for selected quality")
    
    chat_id = selected_quality.get("chat_id")
    
    if not chat_id:
        raise HTTPException(status_code=404, detail="Chat ID not found for selected quality")
    return {
        "msg_id": msg_id,
        "chat_id": chat_id,
        "hash": file_hash
    }