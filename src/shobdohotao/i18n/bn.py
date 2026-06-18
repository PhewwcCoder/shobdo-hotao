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
    "error.invalid_filename": "এই নামটি সঠিক নয়।",
    "error.output_folder_failed": "সংরক্ষণের ফোল্ডার তৈরি করা যায়নি।",
    "error.save_failed": "পরিষ্কার ফাইলটি সংরক্ষণ করা যায়নি।",
    "error.file_locked": "ফাইলটি অন্য একটি প্রোগ্রাম ব্যবহার করছে।",
    "error.cannot_open": "উইন্ডোজ ফাইলটি খুলতে পারেনি।",
    "error.file_missing": "পরিষ্কার ফাইলটি সরানো বা মুছে ফেলা হয়েছে।",
    # Home screen
    "home.no_file": "কোনো ফাইল বাছাই করা হয়নি",
    "home.selected": "বাছাইকৃত:",
    "action.clean_video_audio": "ভিডিওর আওয়াজ দূর করুন",
    "action.cleaned_files": "পরিষ্কার ফাইলসমূহ",
    # Save-cleaned-file dialog
    "save.title": "পরিষ্কার ফাইল সংরক্ষণ করুন",
    "save.filename": "ফাইলের নাম",
    "save.type": "ফাইলের ধরন",
    "save.destination": "যেখানে সংরক্ষণ হবে",
    "save.button": "সংরক্ষণ",
    "save.discard.title": "পরিষ্কার ফাইলটি বাতিল করবেন?",
    "save.discard.body": "আপনি এখনো এই পরিষ্কার ফাইলটি সংরক্ষণ করেননি। "
    "এটি বাতিল করে আবার শুরু করবেন?",
    "save.discard.keep": "সম্পাদনা চালিয়ে যান",
    "save.discard.discard": "বাতিল করুন",
    # Live filename validation
    "validate.empty": "একটি ফাইলের নাম লিখুন।",
    "validate.invalid_chars": "নামে  < > : \" / \\ | ? *  থাকতে পারে না।",
    "validate.reserved": "এই নামটি উইন্ডোজের সংরক্ষিত। অন্য নাম বাছুন।",
    "validate.too_long": "নামটি খুব দীর্ঘ।",
    "validate.trailing": "নাম স্পেস বা ডট দিয়ে শেষ হতে পারে না।",
    # Completion panel
    "completion.ready": "আপনার পরিষ্কার ফাইলটি প্রস্তুত",
    "completion.filename": "নাম",
    "completion.folder": "ফোল্ডার",
    "completion.type": "ধরন",
    "completion.size": "আকার",
    "completion.duration": "দৈর্ঘ্য",
    "action.play_cleaned_file": "পরিষ্কার ফাইল চালান",
    "action.open_cleaned_video": "পরিষ্কার ভিডিও খুলুন",
    "action.show_in_folder": "ফোল্ডারে দেখান",
    "action.clean_another": "আরেকটি ফাইল পরিষ্কার করুন",
    "action.go_to_cleaned_files": "পরিষ্কার ফাইলসমূহে যান",
    # Navigation / shell
    "nav.home": "হোম",
    "nav.cleaned_files": "পরিষ্কার ফাইলসমূহ",
    # Home hero
    "home.hero_statement": "বাংলাদেশে তৈরি একটি উইন্ডোজ অ্যাপ — আপনার অডিও ও "
    "ভিডিও থেকে আওয়াজ দূর করে, সম্পূর্ণ অফলাইনে।",
    # Home drop zone
    "home.drop": "এখানে অডিও বা ভিডিও ফেলুন",
    "home.or_choose": "অথবা ফাইল বেছে নিন",
    "home.supported": "সমর্থিত: MP3, WAV, M4A, FLAC · MP4, MOV, MKV, AVI, WebM",
    "home.reading_file": "ফাইল পড়া হচ্ছে…",
    "home.replace_file": "ফাইল বদলান",
    "media.format": "ফরম্যাট",
    "media.size": "আকার",
    "media.duration": "দৈর্ঘ্য",
    "media.sample_rate": "স্যাম্পল রেট",
    "media.resolution": "রেজোলিউশন",
    "media.audio": "অডিও",
    "media.video": "ভিডিও",
    # Processing view
    "processing.title": "প্রক্রিয়াকরণ",
    "processing.subtitle": "স্থানীয় AI · কোনো আপলোড নেই · CPU · DeepFilterNet3",
    "processing.privacy": "সম্পূর্ণ স্থানীয়ভাবে প্রক্রিয়া করা হয়েছে — কিছুই আপলোড হয় না",
    "processing.elapsed": "অতিবাহিত",
    "processing.stage_of": "ধাপ {current} / {total}",
    "processing.visualization": "প্রক্রিয়াকরণ ভিজ্যুয়ালাইজেশন",
    "processing.engine_log": "ইঞ্জিন লগ",
    "processing.pipeline": "পাইপলাইন",
    "processing.cancel": "প্রক্রিয়া বাতিল করুন",
    "processing.hide_details": "কারিগরি বিবরণ লুকান",
    "console.copy": "কার্যকলাপ কপি করুন",
    "console.pause_scroll": "অটো-স্ক্রল থামান",
    "console.resume_scroll": "অটো-স্ক্রল চালু করুন",
    # Error recovery
    "action.try_again": "আবার চেষ্টা করুন",
    "action.choose_another": "অন্য ফাইল বাছুন",
    "action.view_log_folder": "লগ ফোল্ডার দেখুন",
    # Pipeline stage names (stage.<ProcessingStage value>)
    "stage.preparing": "ফাইল প্রস্তুত করা হচ্ছে",
    "stage.inspecting": "ভিডিও পরীক্ষা করা হচ্ছে",
    "stage.extracting_audio": "অডিও আলাদা করা হচ্ছে",
    "stage.converting": "অডিও রূপান্তর করা হচ্ছে",
    "stage.loading_model": "AI মডেল লোড হচ্ছে",
    "stage.denoising": "আওয়াজ দূর করা হচ্ছে",
    "stage.encoding": "আউটপুট এনকোড করা হচ্ছে",
    "stage.muxing_video": "ভিডিও পুনর্গঠন করা হচ্ছে",
    "stage.finalizing": "ফলাফল সংরক্ষণ করা হচ্ছে",
    "stage.completed": "সম্পন্ন",
    "stage.failed": "ব্যর্থ",
    "stage.cancelled": "বাতিল",
    # Activity log templates (activity.<ActivityCode value>)
    "activity.input_identified": "ইনপুট শনাক্ত: {kind}",
    "activity.audio_stream": "অডিও স্ট্রিম: {codec}, {sample_rate} Hz, {channels} ch",
    "activity.extracting": "অডিও ট্র্যাক আলাদা করা হচ্ছে",
    "activity.converting": "৪৮ kHz-এ অডিও প্রস্তুত করা হচ্ছে",
    "activity.model_ready": "DeepFilterNet3 মডেল প্রস্তুত",
    "activity.denoise_started": "আওয়াজ দূর করা শুরু হয়েছে",
    "activity.analyzing": "ফ্রিকোয়েন্সি স্পেকট্রাম বিশ্লেষণ করা হচ্ছে (STFT · ৪৮ kHz)",
    "activity.profiling_noise": "পেছনের আওয়াজের মাত্রা শনাক্ত করা হচ্ছে",
    "activity.separating": "কণ্ঠস্বর ও আওয়াজ আলাদা করা হচ্ছে",
    "activity.applying_mask": "ফ্রিকোয়েন্সি ব্যান্ডে ডিপ-ফিল্টার মাস্ক প্রয়োগ করা হচ্ছে",
    "activity.reconstructing": "পরিষ্কার শব্দতরঙ্গ পুনর্গঠন করা হচ্ছে",
    "activity.verifying": "ফলাফল যাচাই করা হচ্ছে",
    "activity.ffmpeg_progress": "{total}s-এর মধ্যে {current}s প্রক্রিয়া হয়েছে",
    "activity.rebuilding_video": "পরিষ্কার অডিও দিয়ে ভিডিও পুনর্গঠন করা হচ্ছে",
    "activity.encoding": "পরিষ্কার অডিও এনকোড করা হচ্ছে",
    "activity.saving": "লাইব্রেরিতে ফলাফল সংরক্ষণ করা হচ্ছে",
    "activity.done": "সম্পন্ন",
}
