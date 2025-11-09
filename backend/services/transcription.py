"""
AssemblyAI transcription service
Replaces OpenAI Whisper for ban-proof transcription
"""
import assemblyai as aai
from config.settings import settings
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Configure AssemblyAI
aai.settings.api_key = settings.ASSEMBLYAI_API_KEY


class TranscriptionService:
    """Handle audio/video transcription with AssemblyAI"""

    def __init__(self):
        self.transcriber = aai.Transcriber()

    async def transcribe_file(
        self,
        file_url: str,
        enable_speaker_labels: bool = True,
        language_code: str = "en"
    ) -> Dict:
        """
        Transcribe audio or video file using AssemblyAI

        Args:
            file_url: URL to the audio/video file (can be Supabase Storage URL)
            enable_speaker_labels: Enable speaker diarization (multiple speakers)
            language_code: Language code (default: "en" for English)

        Returns:
            Dict with transcript text, speakers, confidence, etc.
        """
        try:
            logger.info(f"Starting transcription for: {file_url}")

            # Configure transcription
            config = aai.TranscriptionConfig(
                speaker_labels=enable_speaker_labels,
                language_code=language_code,
                punctuate=True,
                format_text=True
            )

            # Start transcription
            transcript = self.transcriber.transcribe(file_url, config=config)

            # Wait for completion
            if transcript.status == aai.TranscriptStatus.error:
                logger.error(f"Transcription failed: {transcript.error}")
                raise Exception(f"Transcription failed: {transcript.error}")

            logger.info(f"Transcription completed. Duration: {transcript.audio_duration}s")

            # Build result
            result = {
                "text": transcript.text,
                "confidence": transcript.confidence,
                "audio_duration": transcript.audio_duration,
                "word_count": len(transcript.text.split()) if transcript.text else 0,
                "language": transcript.language_code,
                "status": "completed"
            }

            # Add speaker labels if enabled
            if enable_speaker_labels and transcript.utterances:
                speakers = []
                for utterance in transcript.utterances:
                    speakers.append({
                        "speaker": utterance.speaker,
                        "text": utterance.text,
                        "start": utterance.start,
                        "end": utterance.end,
                        "confidence": utterance.confidence
                    })
                result["speakers"] = speakers

            # Add words with timestamps (useful for video timestamp linking in Phase 3)
            if transcript.words:
                words = []
                for word in transcript.words[:100]:  # Limit to first 100 for storage
                    words.append({
                        "text": word.text,
                        "start": word.start,
                        "end": word.end,
                        "confidence": word.confidence
                    })
                result["words_sample"] = words

            # Calculate cost (AssemblyAI pricing: ~$0.25 per hour)
            # This is approximate - adjust based on actual pricing
            hours = (transcript.audio_duration / 3600) if transcript.audio_duration else 0
            result["cost_usd"] = round(hours * 0.25, 4)

            return result

        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            raise

    async def transcribe_multiple(
        self,
        file_urls: list[str],
        enable_speaker_labels: bool = True
    ) -> Dict:
        """
        Transcribe multiple audio/video files and merge results

        Args:
            file_urls: List of URLs to audio/video files
            enable_speaker_labels: Enable speaker diarization

        Returns:
            Dict with merged transcript and metadata
        """
        try:
            logger.info(f"Transcribing {len(file_urls)} files...")

            all_transcripts = []
            total_cost = 0.0
            total_duration = 0

            for i, url in enumerate(file_urls, 1):
                logger.info(f"Processing file {i}/{len(file_urls)}")

                result = await self.transcribe_file(
                    url,
                    enable_speaker_labels=enable_speaker_labels
                )

                all_transcripts.append({
                    "file_index": i,
                    "text": result["text"],
                    "duration": result.get("audio_duration", 0),
                    "speakers": result.get("speakers", [])
                })

                total_cost += result.get("cost_usd", 0)
                total_duration += result.get("audio_duration", 0)

            # Merge all transcripts
            merged_text = "\n\n".join([
                f"--- File {t['file_index']} ---\n{t['text']}"
                for t in all_transcripts
            ])

            return {
                "text": merged_text,
                "file_count": len(file_urls),
                "total_duration": total_duration,
                "total_cost_usd": round(total_cost, 4),
                "individual_transcripts": all_transcripts,
                "status": "completed"
            }

        except Exception as e:
            logger.error(f"Error transcribing multiple files: {e}")
            raise


# Global instance
transcription_service = TranscriptionService()


async def transcribe_audio(file_url: str, enable_speaker_labels: bool = True) -> Dict:
    """Convenience function to transcribe a single file"""
    return await transcription_service.transcribe_file(file_url, enable_speaker_labels)


async def transcribe_multiple_files(file_urls: list[str]) -> Dict:
    """Convenience function to transcribe multiple files"""
    return await transcription_service.transcribe_multiple(file_urls)
