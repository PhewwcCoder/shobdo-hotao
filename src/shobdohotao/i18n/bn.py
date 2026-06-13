"""Bangla string catalog. Keys mirror ``en.py`` exactly.

Rendered with a bundled Bangla-capable font (e.g. Noto Sans Bengali) so glyphs
appear correctly on a clean Windows PC without extra installs.
"""

STRINGS: dict[str, str] = {
    # App identity
    "app.title": "শব্দ-হটাও",
    "app.title.native": "শব্দ-হটাও",
    "app.tagline": "আপনার রেকর্ডিং থেকে আওয়াজ দূর করুন — সম্পূর্ণ অফলাইনে।",
    "app.value": "একটি আওয়াজভরা রেকর্ডিং বাছুন, শক্তি বেছে নিন, "
    "‘আওয়াজ দূর করুন’ চাপুন, তুলনা করুন এবং সংরক্ষণ করুন। "
    "কোনো অ্যাকাউন্ট নেই। আপলোড নেই। সীমা নেই।",
    # Primary actions
    "action.open": "ফাইল খুলুন",
    "action.clean": "আওয়াজ দূর করুন",
    "action.cancel": "বাতিল",
    "action.export": "সংরক্ষণ করুন",
    "action.play_original": "আসলটি চালান",
    "action.play_cleaned": "পরিষ্কারটি চালান",
    "action.settings": "সেটিংস",
    # Strength presets
    "strength.gentle": "মৃদু",
    "strength.balanced": "সুষম",
    "strength.strong": "কড়া",
    "strength.label": "শক্তি",
    # Settings
    "settings.output_folder": "সংরক্ষণের ফোল্ডার",
    "settings.output_format": "সংরক্ষণের ধরন",
    "settings.language": "ভাষা",
    "settings.reduce_motion": "নড়াচড়া কমান",
    "settings.reduce_transparency": "সরল থিম (স্বচ্ছতা কমান)",
    # Status
    "status.idle": "প্রস্তুত",
    "status.validating": "ফাইল যাচাই করা হচ্ছে…",
    "status.converting": "অডিও প্রস্তুত করা হচ্ছে…",
    "status.enhancing": "আওয়াজ দূর করা হচ্ছে…",
    "status.exporting": "পরিষ্কার অডিও সংরক্ষণ করা হচ্ছে…",
    "status.done": "সম্পন্ন",
    "status.cancelled": "বাতিল করা হয়েছে",
    # Video stages
    "status.inspecting": "ভিডিও পরীক্ষা করা হচ্ছে…",
    "status.extracting": "অডিও আলাদা করা হচ্ছে…",
    "status.muxing": "পরিষ্কার ভিডিও তৈরি করা হচ্ছে…",
    # Video stream selection
    "video.choose_audio.title": "একটি অডিও ট্র্যাক বাছুন",
    "video.choose_audio.prompt": "এই ভিডিওতে একাধিক অডিও ট্র্যাক আছে। "
    "কোনটি পরিষ্কার করতে চান?",
    "video.open": "ভিডিও খুলুন",
    # Metadata labels
    "meta.duration": "দৈর্ঘ্য",
    "meta.channels": "চ্যানেল",
    "meta.sample_rate": "স্যাম্পল রেট",
    "meta.size": "আকার",
    # First run / privacy
    "firstrun.title": "শব্দ-হটাও-তে স্বাগতম",
    "firstrun.body": "আপনার অডিও কখনো এই কম্পিউটার ছাড়ে না। সমস্ত প্রক্রিয়া "
    "আপনার পিসিতে সম্পূর্ণ অফলাইনে চলে। কোনো অ্যাকাউন্ট নেই, আপলোড নেই, সীমা নেই।",
    "privacy.title": "গোপনীয়তা ও পরিচিতি",
    "privacy.body": "শব্দ-হটাও অডিও সম্পূর্ণ অফলাইনে প্রক্রিয়া করে। কিছুই "
    "আপলোড হয় না, কোনো অ্যাকাউন্ট নেই, কোনো ট্র্যাকিং নেই। অ্যাপের সোর্স MIT লাইসেন্সকৃত।",
    "privacy.disclaimer": "মনে রাখবেন: সব আওয়াজ দূর করা সম্ভব নয়, এবং ফলাফল "
    "স্টুডিও মানের নয়।",
    # Errors (mapped from ErrorCode)
    "error.unknown": "কিছু একটা সমস্যা হয়েছে। আবার চেষ্টা করুন।",
    "error.file_not_found": "ফাইলটি খুঁজে পাওয়া যায়নি।",
    "error.unsupported_format": "এই ধরনের ফাইল সমর্থিত নয়।",
    "error.unsupported_container": "এই ভিডিও ফরম্যাট সমর্থিত নয়।",
    "error.video_too_long": "এই ভিডিওটি প্রক্রিয়া করার জন্য খুব দীর্ঘ।",
    "error.corrupt_media": "ফাইলটি নষ্ট মনে হচ্ছে, পড়া যাচ্ছে না।",
    "error.no_audio_stream": "এই ফাইলে পরিষ্কার করার মতো কোনো অডিও নেই।",
    "error.ffmpeg_failed": "অডিও প্রক্রিয়া করা যায়নি। ফাইলটি নষ্ট হতে পারে।",
    "error.backend_init_failed": "আওয়াজ দূরকারী চালু হয়নি। অ্যাপটি আবার চালু করুন।",
    "error.enhance_failed": "এই ফাইলের আওয়াজ দূর করা যায়নি।",
    "error.output_not_written": "পরিষ্কার ফাইলটি সংরক্ষণ করা যায়নি।",
    "error.low_disk_space": "ফলাফল সংরক্ষণের জন্য যথেষ্ট জায়গা নেই।",
    "error.cancelled": "প্রক্রিয়া বাতিল করা হয়েছে।",
}
