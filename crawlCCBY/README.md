# YouTube Copyright Checker

A Python system to check YouTube videos for copyright restrictions and extract safe content.

## 🎯 Features

- **YouTube API Integration**: Get video details, descriptions, and license information
- **LLM Copyright Analysis**: Use OpenAI to analyze video descriptions for copyright violations
- **Creative Commons Detection**: Automatically detect Creative Commons licensed videos
- **Batch Processing**: Check multiple videos at once
- **Transcription Extraction**: Get video transcriptions for safe videos

## 📋 Requirements

- Python 3.7+
- YouTube API Key
- OpenAI API Key

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd crawlCCBY
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your API keys
   YOUTUBE_API_KEY=your_youtube_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## 🔧 Usage

### Single Video Check

```python
from 2_videoID2Detail2CheckNoCopyWrite import checkVideoCopyrightAndReturnID

# Check if a video is safe to use
video_id = "4MhK5C37_fI"
safe_video_id = checkVideoCopyrightAndReturnID(video_id)

if safe_video_id:
    print(f"✅ Video {safe_video_id} is safe to use!")
else:
    print("❌ Video has copyright restrictions")
```

### Multiple Videos Check

```python
from 2_videoID2Detail2CheckNoCopyWrite import processMultipleVideos

# Check multiple videos
video_ids = ["4MhK5C37_fI", "gwLej8heN5c", "another_video_id"]
safe_videos = processMultipleVideos(video_ids)

print(f"Safe videos: {safe_videos}")
```

### Get Video Details

```python
from 2_videoID2Detail2CheckNoCopyWrite import getVideoDetails, getDescription, getVideoLicense

video_id = "4MhK5C37_fI"

# Get full video details
video_details = getVideoDetails(video_id)
description = getDescription(video_id)
license_info = getVideoLicense(video_id)

print(f"Title: {video_details['snippet']['title']}")
print(f"License: {license_info}")
print(f"Description: {description[:200]}...")
```

## 📁 File Structure

```
crawlCCBY/
├── 1_keywordAndCCBY2VideoID.py          # Search for Creative Commons videos
├── 2_videoID2Detail2CheckNoCopyWrite.py # Main copyright checking system
├── 3_videoIDNoCopyWirte2Transcription2Experience.py # Transcription processing
├── example_usage.py                     # Usage examples
├── test_copyright_check.py              # Test script
├── requirements.txt                     # Python dependencies
├── .env.example                         # Environment variables template
└── README.md                           # This file
```

## 🔍 How It Works

1. **Video Details Retrieval**: Uses YouTube API to get video information including:
   - Title and description
   - License type (Creative Commons vs Standard)
   - Privacy status
   - Channel information

2. **License Check**: Automatically detects if video has Creative Commons license

3. **LLM Analysis**: Uses OpenAI to analyze video description for:
   - Copyright notices (©, Copyright, Bản quyền)
   - Ownership claims
   - Distribution restrictions
   - Trademarked content

4. **Safety Decision**: Returns video ID only if:
   - Video has Creative Commons license AND
   - Description doesn't contain copyright restrictions

## 🧪 Testing

Run the test script to verify everything works:

```bash
python test_copyright_check.py
```

Or run the example usage:

```bash
python example_usage.py
```

## 📊 API Response Example

The system processes YouTube API responses like this:

```json
{
    "items": [
        {
            "snippet": {
                "title": "Video Title",
                "description": "Video description...",
                "channelTitle": "Channel Name"
            },
            "status": {
                "license": "creativeCommon",
                "privacyStatus": "public"
            }
        }
    ]
}
```

## ⚠️ Important Notes

- **API Keys**: Make sure to set your YouTube and OpenAI API keys in the `.env` file
- **Rate Limits**: Be aware of YouTube API rate limits
- **Copyright**: This tool helps identify safe content, but always verify copyright status
- **Costs**: OpenAI API calls have costs - monitor your usage

## 🛠️ Troubleshooting

### Common Issues

1. **API Key Errors**
   ```
   ValueError: YouTube API key not found
   ```
   Solution: Check your `.env` file has the correct API keys

2. **Video Not Found**
   ```
   Error getting video details: 404
   ```
   Solution: Verify the video ID exists and is public

3. **OpenAI Errors**
   ```
   Error: OpenAI API key not found
   ```
   Solution: Set `OPENAI_API_KEY` in your `.env` file

## 📈 Future Enhancements

- [ ] Add support for playlist processing
- [ ] Implement caching for API responses
- [ ] Add more detailed copyright analysis
- [ ] Create web interface
- [ ] Add database storage for results

## 📄 License

This project is for educational purposes. Always respect copyright laws and YouTube's Terms of Service.

