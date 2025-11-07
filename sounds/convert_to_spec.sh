#!/bin/bash
# Convert all WAV files in this directory to standard spec:
# 44.1kHz, 16-bit, mono

for file in *.wav; do
	if [ -f "$file" ]; then
		echo "Converting $file..."
		ffmpeg -i "$file" -ar 44100 -sample_fmt s16 -ac 1 "${file%.wav}_converted.wav" -y
		mv "${file%.wav}_converted.wav" "$file"
		echo "✓ $file converted"
	fi
done

echo ""
echo "All files converted to: 44.1kHz, 16-bit, mono"
