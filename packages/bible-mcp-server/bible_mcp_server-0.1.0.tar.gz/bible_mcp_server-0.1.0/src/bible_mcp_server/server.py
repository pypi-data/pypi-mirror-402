"""
Bible MCP Server

A comprehensive Bible server providing verse lookup, search, study tools, and devotional content using Bible APIs
"""

from fastmcp import FastMCP

# Initialize the MCP server
mcp = FastMCP("Bible MCP Server")

@mcp.tool()
def get_verse(reference: str, translation: str) -> str:
    """Get a specific Bible verse or passage

    Args:
        reference: Bible reference (e.g., 'John 3:16', 'Genesis 1:1-3', 'Psalm 23')
        translation: Bible translation (default: kjv, options: kjv, niv, esv, nlt, nasb)

    Returns:
        The requested Bible verse(s) with reference and translation info
    """
    import requests
    import re
    
    # Parse reference
    reference = reference.strip()
    translation = translation or 'kjv'
    
    # Use bible-api.com for simple access
    try:
        # Format reference for API
        formatted_ref = reference.replace(' ', '%20')
        url = f'https://bible-api.com/{formatted_ref}?translation={translation}'
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                return f"Error: {data['error']}"
            
            result = f"**{data.get('reference', reference)} ({translation.upper()})**\n\n"
            result += data.get('text', 'Text not found').strip()
            return result
        else:
            return f"Error fetching verse: HTTP {response.status_code}"
    except Exception as e:
        return f"Error fetching verse: {str(e)}"

@mcp.tool()
def search_verses(query: str, limit: int) -> str:
    """Search for Bible verses containing specific words or phrases

    Args:
        query: Search term or phrase to find in Bible verses
        limit: Maximum number of results to return (default: 10, max: 50)

    Returns:
        List of Bible verses containing the search term
    """
    import requests
    import json
    
    query = query.strip()
    limit = min(limit or 10, 50)
    
    # Use a simple search approach with common verses
    # This is a basic implementation - in production you'd use a proper Bible search API
    try:
        # For demo purposes, using a basic verse database approach
        # You could integrate with APIs like API.Bible for better search
        
        common_verses = {
            'love': ['John 3:16', '1 Corinthians 13:4-7', '1 John 4:8'],
            'peace': ['John 14:27', 'Philippians 4:6-7', 'Isaiah 26:3'],
            'faith': ['Hebrews 11:1', 'Romans 10:17', 'Ephesians 2:8-9'],
            'hope': ['Jeremiah 29:11', 'Romans 15:13', 'Hebrews 11:1'],
            'joy': ['Nehemiah 8:10', 'Psalm 16:11', 'John 15:11'],
            'strength': ['Isaiah 40:31', 'Philippians 4:13', 'Psalm 46:1'],
            'wisdom': ['Proverbs 3:5-6', 'James 1:5', 'Proverbs 9:10'],
            'forgiveness': ['1 John 1:9', 'Ephesians 4:32', 'Matthew 6:14-15']
        }
        
        query_lower = query.lower()
        results = []
        
        for keyword, verses in common_verses.items():
            if keyword in query_lower or query_lower in keyword:
                for verse_ref in verses[:limit]:
                    # Get the actual verse text
                    url = f'https://bible-api.com/{verse_ref.replace(" ", "%20")}'
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if 'error' not in data:
                            results.append({
                                'reference': data.get('reference', verse_ref),
                                'text': data.get('text', '').strip()
                            })
                    if len(results) >= limit:
                        break
        
        if not results:
            return f"No verses found for '{query}'. Try terms like: love, peace, faith, hope, joy, strength, wisdom, forgiveness"
        
        output = f"**Search Results for '{query}' ({len(results)} found):**\n\n"
        for i, verse in enumerate(results, 1):
            output += f"{i}. **{verse['reference']}**\n{verse['text']}\n\n"
        
        return output.strip()
        
    except Exception as e:
        return f"Error searching verses: {str(e)}"

@mcp.tool()
def get_random_verse(category: str) -> str:
    """Get a random Bible verse for inspiration or daily reading

    Args:
        category: Optional category (encouragement, wisdom, love, peace, strength, faith)

    Returns:
        A random Bible verse with reference
    """
    import requests
    import random
    
    # Curated lists of verses by category
    verse_collections = {
        'encouragement': [
            'Joshua 1:9', 'Isaiah 41:10', 'Philippians 4:13', 'Psalm 23:4',
            'Romans 8:28', 'Jeremiah 29:11', 'Isaiah 40:31', 'Psalm 46:1'
        ],
        'wisdom': [
            'Proverbs 3:5-6', 'James 1:5', 'Proverbs 27:17', 'Ecclesiastes 3:1',
            'Proverbs 16:3', 'Psalm 119:105', 'Proverbs 19:20', 'Matthew 7:7'
        ],
        'love': [
            'John 3:16', '1 Corinthians 13:4-7', '1 John 4:19', 'Romans 8:38-39',
            'Ephesians 3:17-19', '1 John 4:8', 'John 13:34-35', 'Romans 5:8'
        ],
        'peace': [
            'John 14:27', 'Philippians 4:6-7', 'Isaiah 26:3', 'Matthew 11:28-30',
            'Romans 12:18', 'Colossians 3:15', 'Psalm 29:11', '2 Thessalonians 3:16'
        ],
        'strength': [
            'Philippians 4:13', 'Isaiah 40:31', 'Psalm 46:1', '2 Corinthians 12:9',
            'Nehemiah 8:10', 'Psalm 27:1', 'Ephesians 6:10', 'Deuteronomy 31:6'
        ],
        'faith': [
            'Hebrews 11:1', 'Romans 10:17', 'Ephesians 2:8-9', 'Matthew 17:20',
            'Habakkuk 2:4', '2 Corinthians 5:7', 'Romans 1:17', 'Mark 9:23'
        ]
    }
    
    try:
        if category and category.lower() in verse_collections:
            verses = verse_collections[category.lower()]
            selected_verse = random.choice(verses)
            category_note = f" (Category: {category.title()})"
        else:
            # Random from all verses
            all_verses = []
            for cat_verses in verse_collections.values():
                all_verses.extend(cat_verses)
            selected_verse = random.choice(all_verses)
            category_note = ""
        
        # Get the verse text
        url = f'https://bible-api.com/{selected_verse.replace(" ", "%20")}'
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'error' in data:
                return f"Error: {data['error']}"
            
            result = f"**Daily Verse{category_note}**\n\n"
            result += f"**{data.get('reference', selected_verse)}**\n\n"
            result += data.get('text', 'Text not found').strip()
            result += "\n\n*May this verse bring you encouragement today.*"
            return result
        else:
            return f"Error fetching random verse: HTTP {response.status_code}"
            
    except Exception as e:
        return f"Error getting random verse: {str(e)}"

@mcp.tool()
def get_chapter_info(book: str, chapter: int) -> str:
    """Get information about a Bible book or chapter, including verse count and summary

    Args:
        book: Bible book name (e.g., 'Genesis', 'John', 'Psalms')
        chapter: Chapter number (optional, if not provided, gives book info)

    Returns:
        Information about the requested Bible book or chapter
    """
    # Bible book information database
    book_info = {
        'genesis': {'chapters': 50, 'testament': 'Old', 'author': 'Moses', 'theme': 'Beginnings'},
        'exodus': {'chapters': 40, 'testament': 'Old', 'author': 'Moses', 'theme': 'Deliverance'},
        'psalms': {'chapters': 150, 'testament': 'Old', 'author': 'Various (David, etc.)', 'theme': 'Worship and Prayer'},
        'proverbs': {'chapters': 31, 'testament': 'Old', 'author': 'Solomon (mainly)', 'theme': 'Wisdom'},
        'ecclesiastes': {'chapters': 12, 'testament': 'Old', 'author': 'Solomon', 'theme': 'Meaning of Life'},
        'matthew': {'chapters': 28, 'testament': 'New', 'author': 'Matthew', 'theme': 'Jesus as King'},
        'mark': {'chapters': 16, 'testament': 'New', 'author': 'Mark', 'theme': 'Jesus as Servant'},
        'luke': {'chapters': 24, 'testament': 'New', 'author': 'Luke', 'theme': 'Jesus as Man'},
        'john': {'chapters': 21, 'testament': 'New', 'author': 'John', 'theme': 'Jesus as God'},
        'acts': {'chapters': 28, 'testament': 'New', 'author': 'Luke', 'theme': 'Early Church'},
        'romans': {'chapters': 16, 'testament': 'New', 'author': 'Paul', 'theme': 'Salvation by Faith'},
        'ephesians': {'chapters': 6, 'testament': 'New', 'author': 'Paul', 'theme': 'Unity in Christ'},
        'philippians': {'chapters': 4, 'testament': 'New', 'author': 'Paul', 'theme': 'Joy in Christ'},
        'revelation': {'chapters': 22, 'testament': 'New', 'author': 'John', 'theme': 'End Times'}
    }
    
    book_lower = book.lower().strip()
    
    if book_lower not in book_info:
        available_books = ', '.join(sorted(book_info.keys()))
        return f"Book '{book}' not found. Available books: {available_books}"
    
    info = book_info[book_lower]
    result = f"**Book of {book.title()}**\n\n"
    result += f"**Testament:** {info['testament']} Testament\n"
    result += f"**Author:** {info['author']}\n"
    result += f"**Chapters:** {info['chapters']}\n"
    result += f"**Theme:** {info['theme']}\n\n"
    
    if chapter:
        if chapter > info['chapters']:
            result += f"Error: {book.title()} only has {info['chapters']} chapters."
        else:
            result += f"**Chapter {chapter} Information:**\n"
            result += f"This is chapter {chapter} of {info['chapters']} in {book.title()}.\n\n"
            
            # Try to get the chapter text
            try:
                import requests
                url = f'https://bible-api.com/{book.lower()}+{chapter}'
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'error' not in data and 'verses' in data:
                        verse_count = len(data['verses'])
                        result += f"**Verses in this chapter:** {verse_count}\n\n"
                        result += f"**First verse:** {data['verses'][0]['text'][:100]}..."
            except:
                result += "Chapter details available upon request."
    else:
        result += f"*Use chapter parameter to get specific chapter information.*"
    
    return result

@mcp.tool()
def compare_translations(reference: str, translations: str) -> str:
    """Compare a Bible verse across different translations

    Args:
        reference: Bible reference to compare (e.g., 'John 3:16')
        translations: Comma-separated list of translations (default: kjv,niv,esv) - options: kjv,niv,esv,nlt,nasb

    Returns:
        The verse in multiple translations for comparison
    """
    import requests
    import time
    
    reference = reference.strip()
    translations_input = translations or 'kjv,niv,esv'
    translation_list = [t.strip().lower() for t in translations_input.split(',')]
    
    # Validate translations
    valid_translations = ['kjv', 'niv', 'esv', 'nlt', 'nasb']
    translation_list = [t for t in translation_list if t in valid_translations]
    
    if not translation_list:
        return "Error: No valid translations specified. Valid options: kjv, niv, esv, nlt, nasb"
    
    result = f"**{reference} - Translation Comparison**\n\n"
    
    for translation in translation_list:
        try:
            formatted_ref = reference.replace(' ', '%20')
            url = f'https://bible-api.com/{formatted_ref}?translation={translation}'
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    result += f"**{translation.upper()}:**\n"
                    result += f"{data.get('text', 'Text not found').strip()}\n\n"
                else:
                    result += f"**{translation.upper()}:** Error - {data['error']}\n\n"
            else:
                result += f"**{translation.upper()}:** Error fetching (HTTP {response.status_code})\n\n"
            
            # Small delay to be respectful to API
            time.sleep(0.5)
            
        except Exception as e:
            result += f"**{translation.upper()}:** Error - {str(e)}\n\n"
    
    result += "*Compare these translations to gain deeper understanding of the verse.*"
    return result

@mcp.resource("bible://books/{testament}")
def bible_books() -> str:
    """List of all Bible books with basic information"""
    testament = uri.split('/')[-1] if '/' in uri else 'all'
    
    old_testament_books = [
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy',
        'Joshua', 'Judges', 'Ruth', '1 Samuel', '2 Samuel',
        '1 Kings', '2 Kings', '1 Chronicles', '2 Chronicles', 'Ezra',
        'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs',
        'Ecclesiastes', 'Song of Solomon', 'Isaiah', 'Jeremiah', 'Lamentations',
        'Ezekiel', 'Daniel', 'Hosea', 'Joel', 'Amos',
        'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi'
    ]
    
    new_testament_books = [
        'Matthew', 'Mark', 'Luke', 'John', 'Acts',
        'Romans', '1 Corinthians', '2 Corinthians', 'Galatians', 'Ephesians',
        'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', '1 Timothy',
        '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James',
        '1 Peter', '2 Peter', '1 John', '2 John', '3 John',
        'Jude', 'Revelation'
    ]
    
    if testament.lower() == 'old':
        books = old_testament_books
        title = 'Old Testament Books'
    elif testament.lower() == 'new':
        books = new_testament_books
        title = 'New Testament Books'
    else:
        books = old_testament_books + new_testament_books
        title = 'All Bible Books'
    
    result = f'**{title} ({len(books)} books)**\n\n'
    for i, book in enumerate(books, 1):
        result += f'{i}. {book}\n'
    
    result += '\n*Use get_chapter_info tool for detailed information about any book.*'
    return result

@mcp.resource("bible://popular/{category}")
def popular_verses() -> str:
    """Collection of popular and frequently referenced Bible verses"""
    category = uri.split('/')[-1] if '/' in uri else 'all'
    
    popular_verses = {
        'salvation': [
            'John 3:16 - For God so loved the world...',
            'Romans 10:9 - If you confess with your mouth...',
            'Ephesians 2:8-9 - For by grace you have been saved...'
        ],
        'comfort': [
            'Psalm 23:4 - Even though I walk through the valley...',
            'Matthew 11:28 - Come to me, all who are weary...',
            'Isaiah 41:10 - Fear not, for I am with you...'
        ],
        'guidance': [
            'Proverbs 3:5-6 - Trust in the Lord with all your heart...',
            'Psalm 119:105 - Your word is a lamp to my feet...',
            'Jeremiah 29:11 - For I know the plans I have for you...'
        ],
        'love': [
            '1 Corinthians 13:4-7 - Love is patient and kind...',
            '1 John 4:8 - God is love',
            'John 13:35 - By this all people will know...'
        ]
    }
    
    if category.lower() in popular_verses:
        verses = popular_verses[category.lower()]
        result = f'**Popular {category.title()} Verses**\n\n'
        for verse in verses:
            result += f'• {verse}\n'
    else:
        result = '**Popular Bible Verses by Category**\n\n'
        for cat, verses in popular_verses.items():
            result += f'**{cat.title()}:**\n'
            for verse in verses:
                result += f'  • {verse}\n'
            result += '\n'
    
    result += '\n*Use get_verse tool to read the complete text of any verse.*'
    return result

@mcp.prompt()
def bible_study_guide(passage: str, study_type: str) -> str:
    """Generate a Bible study guide for a specific passage or topic

    Args:
        passage: Bible passage or topic to study
        study_type: Type of study (personal, group, devotional, expository)
    """
    return f"""Create a comprehensive Bible study guide for {passage}.

Study Type: {study_type or 'personal study'}

Please include:

1. **Context & Background**
   - Historical setting
   - Author and audience
   - Purpose of the passage

2. **Key Verses & Themes**
   - Main verses to focus on
   - Central themes and messages
   - Cross-references to related passages

3. **Discussion Questions**
   - What does this passage teach about God?
   - How does this apply to our daily lives?
   - What challenges or encouragement do we find here?

4. **Practical Application**
   - Specific ways to apply these truths
   - Action steps for the week
   - Prayer points

5. **Further Study**
   - Related passages to explore
   - Additional resources or commentaries

Make this study guide engaging and practical for spiritual growth."""

@mcp.prompt()
def sermon_outline(text: str, theme: str, audience: str) -> str:
    """Create a sermon outline based on a Bible passage

    Args:
        text: Bible text or passage for the sermon
        theme: Main theme or focus of the sermon
        audience: Target audience (general congregation, youth, etc.)
    """
    return f"""Create a sermon outline based on {text} with the theme: "{theme}"

Audience: {audience or 'general congregation'}

**SERMON OUTLINE**

**Title:** [Compelling sermon title based on the text and theme]

**Text:** {text}

**Main Theme:** {theme}

**I. INTRODUCTION** (5-7 minutes)
- Hook: [Attention-grabbing opening]
- Context: [Brief background of the passage]
- Preview: [What we'll discover today]

**II. EXPOSITION** (20-25 minutes)
- Point 1: [First major truth from the text]
  - Supporting verses
  - Illustration or example
  - Application

- Point 2: [Second major truth]
  - Supporting verses
  - Illustration or example
  - Application

- Point 3: [Third major truth]
  - Supporting verses
  - Illustration or example
  - Application

**III. CONCLUSION** (5 minutes)
- Summary of main points
- Call to action
- Closing prayer focus

**ADDITIONAL NOTES:**
- Key illustrations to consider
- Cross-references for deeper study
- Potential objections to address
- Follow-up study suggestions

Prepare this message to clearly communicate {theme} through {text} in a way that transforms lives."""

@mcp.prompt()
def devotional_reflection(verse: str, life_situation: str) -> str:
    """Generate a personal devotional reflection on a Bible verse or passage

    Args:
        verse: Bible verse or short passage for reflection
        life_situation: Current life situation or challenge to apply the verse to
    """
    return f"""**Daily Devotional Reflection**

**Scripture:** {verse}

**REFLECT**
Take a moment to read {verse} slowly and thoughtfully. What stands out to you in this passage? What is God saying through these words?

**APPLY**
{life_situation and f'Considering your current situation with {life_situation}, how does this verse speak to your circumstances? ' or ''}How can you apply the truth of this verse to your daily life? What specific actions or attitudes might God be calling you to embrace?

**PRAY**
Spend time in prayer, asking God to help you:
- Understand this verse more deeply
- Apply its truth to your life
- Trust in God's faithfulness
{life_situation and f'- Find His guidance regarding {life_situation}' or ''}

**REMEMBER**
Choose one key phrase or truth from {verse} to carry with you throughout the day. Write it down, memorize it, or set it as a reminder on your phone.

**SHARE**
Consider sharing this verse or its impact on you with someone else today - whether through encouragement, prayer, or testimony.

May God bless you as you meditate on His Word and seek to live according to His truth."""

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
