"""
Sample C1-C2 English Vocabulary
Run this script to populate the database with starter words.
"""

import asyncio
import database as db

# C1-C2 Advanced English Vocabulary
SAMPLE_WORDS = [
    # Academic & Formal
    {"word": "ubiquitous", "definition": "present, appearing, or found everywhere", "example": "Smartphones have become ubiquitous in modern society."},
    {"word": "ephemeral", "definition": "lasting for a very short time", "example": "Fame can be ephemeral in the age of social media."},
    {"word": "juxtapose", "definition": "place side by side for comparison or contrast", "example": "The artist juxtaposed light and darkness in her paintings."},
    {"word": "paradigm", "definition": "a typical example or pattern of something", "example": "The discovery shifted the paradigm of scientific thinking."},
    {"word": "quintessential", "definition": "representing the most perfect example of a quality", "example": "She is the quintessential professional—always prepared and courteous."},
    {"word": "idiosyncratic", "definition": "peculiar or individual; distinctive", "example": "His idiosyncratic teaching style made him memorable."},
    {"word": "commensurate", "definition": "corresponding in size or degree; proportionate", "example": "Her salary was commensurate with her experience."},
    {"word": "convoluted", "definition": "extremely complex and difficult to follow", "example": "The legal document was so convoluted that we needed a lawyer."},
    {"word": "esoteric", "definition": "intended for or understood by only a small group", "example": "The professor's lectures on quantum mechanics were quite esoteric."},
    {"word": "sycophant", "definition": "a person who flatters someone important for personal gain", "example": "The CEO was surrounded by sycophants who agreed with everything he said."},
    
    # Descriptive & Literary
    {"word": "mellifluous", "definition": "sweet-sounding; pleasant to hear", "example": "Her mellifluous voice captivated the entire audience."},
    {"word": "ineffable", "definition": "too great or extreme to be expressed in words", "example": "The beauty of the sunset was ineffable."},
    {"word": "serendipitous", "definition": "occurring by chance in a happy way", "example": "Our meeting was completely serendipitous—we were both at the wrong address!"},
    {"word": "surreptitious", "definition": "kept secret, especially because improper", "example": "He cast a surreptitious glance at his phone during the meeting."},
    {"word": "perfunctory", "definition": "carried out without real interest or effort", "example": "His perfunctory apology did nothing to ease the tension."},
    
    # Emotional & Psychological
    {"word": "vicarious", "definition": "experienced through imaginative participation in another's experience", "example": "I get vicarious pleasure from watching travel documentaries."},
    {"word": "cathartic", "definition": "providing psychological relief through expression of emotions", "example": "Writing in her journal was cathartic after the stressful day."},
    {"word": "ambivalent", "definition": "having mixed feelings about something", "example": "She felt ambivalent about accepting the job offer abroad."},
    {"word": "vindictive", "definition": "having a strong desire for revenge", "example": "His vindictive nature made him a difficult colleague."},
    {"word": "benevolent", "definition": "well-meaning and kindly", "example": "The benevolent donor funded the entire scholarship program."},
    
    # Business & Professional
    {"word": "leverage", "definition": "use something to maximum advantage", "example": "We need to leverage our existing customer base for the new product launch."},
    {"word": "synergy", "definition": "combined effect greater than individual effects", "example": "The merger created synergy between the two companies' strengths."},
    {"word": "mitigate", "definition": "make less severe or serious", "example": "We took steps to mitigate the environmental impact of the project."},
    {"word": "streamline", "definition": "make more efficient by simplifying", "example": "The new software will streamline our workflow significantly."},
    {"word": "proliferate", "definition": "increase rapidly in number; multiply", "example": "Fake news tends to proliferate on social media platforms."},
    
    # Abstract & Philosophical
    {"word": "dichotomy", "definition": "a division into two contrasting things", "example": "There's a false dichotomy between economic growth and environmental protection."},
    {"word": "zeitgeist", "definition": "the defining spirit or mood of a particular period", "example": "The film captured the zeitgeist of the 1990s perfectly."},
    {"word": "nuance", "definition": "a subtle difference in meaning or expression", "example": "The translation failed to capture the nuances of the original text."},
    {"word": "paradigm shift", "definition": "a fundamental change in approach or assumptions", "example": "Remote work has caused a paradigm shift in how we think about offices."},
    {"word": "cognitive dissonance", "definition": "mental discomfort from holding contradictory beliefs", "example": "He experienced cognitive dissonance when his actions conflicted with his values."},
    
    # Phrases & Idioms (C1-C2)
    {"word": "a double-edged sword", "definition": "something with both positive and negative effects", "example": "Social media is a double-edged sword—it connects but also isolates."},
    {"word": "the elephant in the room", "definition": "an obvious problem no one wants to discuss", "example": "His poor performance was the elephant in the room during the meeting."},
    {"word": "to play devil's advocate", "definition": "to argue against something for the sake of debate", "example": "Let me play devil's advocate here—what if the plan fails?"},
    {"word": "to turn a blind eye", "definition": "to deliberately ignore something", "example": "Management turned a blind eye to the safety violations."},
    {"word": "to be on the same wavelength", "definition": "to think similarly; to understand each other well", "example": "We were on the same wavelength from the very first meeting."},
    {"word": "to bite off more than you can chew", "definition": "to take on more responsibility than you can handle", "example": "Taking three courses while working full-time—she bit off more than she could chew."},
    {"word": "to cut corners", "definition": "to do something in the easiest or cheapest way", "example": "The construction company cut corners, and now the building has structural issues."},
    {"word": "to be in the same boat", "definition": "to be in the same difficult situation", "example": "We're all in the same boat with these new regulations."},
    {"word": "a blessing in disguise", "definition": "something that seems bad but turns out good", "example": "Losing that job was a blessing in disguise—it led me to my dream career."},
    {"word": "food for thought", "definition": "something that warrants serious consideration", "example": "The documentary provided food for thought about our consumption habits."},
    
    # More Advanced Vocabulary
    {"word": "acquiesce", "definition": "accept something reluctantly but without protest", "example": "She acquiesced to her parents' wishes and studied medicine."},
    {"word": "exacerbate", "definition": "make a problem or situation worse", "example": "The lack of communication only exacerbated the conflict."},
    {"word": "precipitate", "definition": "cause something to happen suddenly or unexpectedly", "example": "The scandal precipitated his resignation."},
    {"word": "ameliorate", "definition": "make something bad better", "example": "The new policies were designed to ameliorate working conditions."},
    {"word": "obfuscate", "definition": "make obscure, unclear, or unintelligible", "example": "Politicians often obfuscate the truth with complicated language."},
    {"word": "galvanize", "definition": "shock or excite into taking action", "example": "The tragedy galvanized the community into demanding change."},
    {"word": "oscillate", "definition": "move back and forth; waver between positions", "example": "She oscillated between excitement and anxiety about the move."},
    {"word": "extrapolate", "definition": "extend the application of something to an unknown situation", "example": "We can extrapolate from current trends what the market might look like."},
    {"word": "inundate", "definition": "overwhelm with things to be dealt with", "example": "After the announcement, we were inundated with applications."},
    {"word": "disseminate", "definition": "spread information widely", "example": "The organization works to disseminate knowledge about climate change."},
]


async def populate_database():
    """Populate the database with sample vocabulary."""
    await db.init_database()
    
    print("Adding sample C1-C2 vocabulary to database...")
    word_ids = await db.add_words_bulk(SAMPLE_WORDS)
    
    print(f"✅ Added {len(word_ids)} words to the database!")
    print("\nSample words added:")
    for i, word_data in enumerate(SAMPLE_WORDS[:10], 1):
        print(f"  {i}. {word_data['word']}")
    print(f"  ... and {len(SAMPLE_WORDS) - 10} more!")
    
    total = await db.get_word_count()
    print(f"\n📊 Total words in database: {total}")


if __name__ == "__main__":
    asyncio.run(populate_database())
