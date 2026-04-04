from moviepy.editor import VideoFileClip, concatenate_videoclips

# Test with just a few seconds
video = VideoFileClip("movie.mp4")
clip1 = video.subclip(0, 1)
clip2 = video.subclip(2, 3)
result = concatenate_videoclips([clip1, clip2])
result.write_videofile("minimal_test.mp4", codec='libx264', preset='ultrafast')
