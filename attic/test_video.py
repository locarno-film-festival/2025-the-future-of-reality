from robust_music_video_generator import RobustMusicVideoGenerator

# Create music video
generator = RobustMusicVideoGenerator("movie.mp4", "song.mp3", "output.mp4")
generator.generate_music_video(style="sequential", max_clips=1000)
