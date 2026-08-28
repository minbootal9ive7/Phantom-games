import os
import asyncio
import random
import discord
from discord.ext import commands
import config
import games

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

mafia_games, chairs_games, roulette_games, bus_games = {}, {}, {}, {}

ARABIC_LETTERS = list("ابتثجحخدذرزسشصضطظعغفقكلمنهوي")
BUS_CATEGORIES = ["اسم", "جماد", "حيوان", "نبات", "بلاد"]

VALID_BUS_WORDS = {
    "اسم": {
        'ا': ["احمد", "ابراهيم", "اسماعيل", "ايمن", "اسامة", "امين", "اسراء", "اية", "امل", "اميرة", "انجي", "امجد", "اسعد", "انور", "ايوب", "إسحاق", "إلياس", "إهاب", "أزهار", "آسر", "أمينة", "أريج", "آيات", "أروى", "آسيا", "أفنان", "إنجي", "ابتسام", "ابتهال", "إحسان", "إخلاص", "أحلام", "أديبة", "أريج", "أزهار", "أسمهان", "إسراء", "أفراح", "أكابر", "أمال", "أميمة", "أمينة", "أنيسة", "أوهام", "إيمان", "ايناس", "إيلاف", "أثير", "أريام", "أسيل", "ألين", "أمل", "أميرة", "أوركيد", "إيبا", "إيثار"],
        'ب': ["باسم", "بهاء", "بلال", "بركات", "بدر", "بتول", "بثينة", "بسام", "بكر", "بشير", "بالغ", "بديع", "براء", "برهان", "بصير", "بنان", "بسملة", "بسمة", "بشرى", "بلقيس", "بهية", "بيان", "بدرية", "باجس", "باهي", "بتال", "بدر الدين", "بدران", "بركات", "بسامة", "بسيمة", "بليغ", "بهجت"],
        'ت': ["تامر", "توفيق", "تميم", "تقى", "تحية", "تيسير", "تركي", "تائر", "تالد", "تميمة", "تغريد", "تواريف", "توحيد", "تولين", "تيمور", "تنوير", "تهاني", "تولاي", "تنسيم", "تسنيم", "تمارة", "تالدة", "تالد", "تامرة"],
        'ث': ["ثامر", "ثابت", "ثريا", "ثروت", "ثائر", "ثناء", "ثراء", "ثقيف", "ثويبة", "ثنيان", "ثوبان", "ثقيل", "ثمد", "ثويبي"],
        'ج': ["جمال", "جلال", "جابر", "جهاد", "جميلة", "جومانة", "جاسر", "جودي", "جليلة", "جابر", "جودت", "جيهان", "جوانا", "جنا", "جوري", "جنان", "جليلة", "جنات", "جمال", "جوهره", "جاسرة", "جواد", "جوي", "جياب", "جبران", "جبر", "جبريل", "جحا"],
        'ح': ["حسن", "حسين", "حامد", "حلمي", "حنان", "حليمة", "حورية", "حازم", "حمدي", "حسنين", "حسان", "حياة", "حسناء", "حورية", "حلا", "حنين", "حبيبة", "حور", "حكمة", "حكمت", "حكيم", "حمود", "حنينة", "حنيفة", "حيدر", "حرب", "حارث", "حذيفة", "حنيش"],
        'خ': ["خالد", "خليل", "خميس", "خديجة", "خلود", "خيري", "خالدة", "خولة", "خنساء", "خضرة", "خزيمة", "خضر", "خطاب", "خريبط", "خازن", "خياط"],
        'د': ["داود", "داليا", "دعاء", "دينا", "دني", "دانة", "دلال", "درة", "ديمة", "داغر", "داني", "درويش", "دبس", "داوود", "درياء", "دياب", "دبيس", "دحام"],
        'ذ': ["ذكي", "ذكريات", "ذو الفقار", "ذيب", "ذاكر", "ذهب", "ذبيان", "ذكري", "ذو النون", "ذليل"],
        'ر': ["رامي", "رجب", "رشدي", "رضا", "رانيا", "رحمة", "ريم", "رائد", "راضي", "رشا", "رواء", "روان", "رنا", "رؤى", "رفعت", "رمزي", "ريناد", "رويدا", "ركان", "رغد", "رباب", "ربية", "رودينا", "رسلان", "رفيق", "رئيس", "ريان", "ريماس", "ريهام"],
        'ز': ["زياد", "زكريا", "زينب", "زهراء", "زينة", "زهران", "زكي", "زهير", "زهرة", "زين", "زكية", "زمردة", "زرياب", "زامل", "زاهر", "زاهي", "زريعة"],
        'س': ["سامح", "سعيد", "سليم", "سامي", "سارة", "سلوى", "سحر", "سعد", "سفيان", "سلطان", "سندس", "سماح", "سميرة", "سناء", "سوزان", "سهر", "سجی", "سيرين", "سيف", "سرمد", "سراج", "سليمى", "سليمان", "سالم", "سلامة", "سعيدان", "سالمة", "سوسن", "سهير", "سمير", "سيد"],
        'ش': ["شريف", "شفيق", "صلاح", "شروق", "شيماء", "شاكر", "شادي", "شهاب", "شوقي", "شيرين", "شهد", "شذا", "شريفة", "شهيرة", "شموس", "شريف", "شعلان", "شيبان", "شبيب", "شقران"],
        'ص': ["صلاح", "صقر", "صفاء", "صباح", "صالح", "صفوت", "صابر", "صاوي", "صادق", "صعبي", "صهيب", "صفية", "صبوحة", "صغيرة", "صمود", "صلاح الدين"],
        'ض': ["ضياء", "ضاحي", "ضحى", "ضاري", "ضرار", "ضحي", "ضي", "ضحيان", "ضفدع", "ضالعة"],
        'ط': ["طارق", "طه", "طلعت", "طيب", "فاطمة", "طالب", "طلحة", "طريف", "طاهرة", "طيبة", "طيف", "طربية", "طرفة", "طعان", "طبيخ"],
        'ظ': ["ظافر", "ظريف", "ظريفة", "ظاهر", "ظبيان", "ظاهرة", "ظليمة", "ظليمة"],
        'ع': ["علي", "عمر", "عثمان", "عصام", "عادل", "عائشة", "عزيزة", "عماد", "علاء", "عارف", "عفيف", "عبي", "عيدة", "علا", "عطيات", "عفراء", "عنود", "عروبة", "عباس", "عقيل", "عقيلة", "عزام", "عساف", "عطية", "عطارد"],
        'غ': ["غالب", "غسان", "غادة", "غزلان", "غالبة", "غصون", "غيدة", "غفران", "غدير", "غيد", "غادة", "غيث", "غزال", "غيثة", "غامد", "غنام"],
        'ف': ["فهد", "فاروق", "فؤاد", "فاطمة", "فريدة", "فرح", "فادي", "فوزي", "فايز", "فائزة", "فتحية", "فردوس", "فريال", "فؤادة", "فدوى", "فتوح", "فاطمة الزهراء", "فراس", "فيصل", "فرحان", "فراج", "فارس"],
        'ق': ["قاسم", "قيس", "قمر", "قادر", "قطز", "قصي", "قاعدة", "قمراء", "قرة العين", "قحطان", "قيس", "قتيبة", "قناص"],
        'ك': ["كريم", "كمال", "كاظم", "كريمة", "كندا", "كارم", "كاميليا", "كوثر", "كرم", "كليوباترا", "كفاح", "كفاح", "كوكب", "كرار", "كليب", "كثير"],
        'ل': ["لطفي", "لقمان", "ليلى", "لمياء", "لبنى", "لمى", "لجين", "لؤي", "لميس", "لينا", "ليان", "لطيفة", "لولوة", "لبيبة", "لهب", "لحيان", "لقمان"],
        'م': ["محمد", "محمود", "مصطفى", "معاذ", "مريم", "منى", "مها", "ماجد", "منصور", "مجدي", "مروة", "مي", "ميرفت", "منال", "ميسون", "ماجدة", "ماهر", "منيب", "منير", "مراد", "محسن", "موسى", "ميساء", "ملك"],
        'ن': ["نبيل", "ناصر", "نادر", "نورا", "نهى", "نجلاء", "نرمین", "نادية", "نجيب", "نجلاء", "نواف", "نوف", "نسرين", "نور", "نهاد", "نعمة", "ناهد", "نشمي", "نايف", "نزار"],
        'ه': ["هاني", "هشام", "هيثم", "هالة", "هدى", "هند", "هناء", "هاجر", "هبة", "هيام", "هانم", "هيام", "هيثم", "هادي", "هادية", "هود", "هلال", "همام"],
        'و': ["وليد", "وائل", "وحيد", "وداد", "وفاء", "وسام", "وجدي", "وائل", "وسيمة", "وردة", "واصف", "وصال", "وائل", "ونيس", "وهيب", "وئام"],
        'ي': ["يوسف", "ياسر", "يحيى", "ياسمين", "يسرا", "يامن", "يمنى", "يعقوب", "ياسين", "يمن", "يسري", "يزيد", "يونس", "ياسمينا", "يمامة", "يامنة"]
    },
    "جماد": {
        'ا': ["ابريق", "ابر", "استيكة", "اسطوانة", "اسفنج", "اباجورة", "اسفلت", "اساور", "ابواب", "ارضية", "الماس", "اسمنت", "اسطوانة", "استاند", "اساس", "ابريق شاي", "ادوات", "اقلام"],
        'ب': ["باب", "برطمان", "برج", "برواز", "بطانية", "بطارية", "براد", "بركة", "برميل", "بستون", "بلاستيك", "بندقية", "بوصلة", "بلكونة", "برواز صور", "بوابه", "بطاقة", "بنزين"],
        'ت': ["تاج", "تلفزيون", "تليفون", "تفاح", "ترابيزة", "تيشيرت", "ترمس", "تلاجة", "تلفاز", "تمثال", "توت", "تذكرة", "تروسيكل", "تسريحة", "تاسوع", "تكييف", "تراب", "تنجيد"],
        'ث': ["ثلاجة", "ثوب", "ثقب", "ثريا", "ثلاجة حفظ", "ثوب نسائي", "ثقل", "ثرموستات", "ثوب نوم", "ثروة"],
        'ج': ["جدار", "جرس", "جزمة", "جوارب", "جيتار", "جسر", "جريدة", "جوارب", "جوال", "جيب", "جناح", "جرافة", "جهاز", "جمجمة", "جلابيات", "جاموسة"],
        'ح': ["حزام", "حقيبة", "حائط", "حديد", "حوض", "حبل", "حائط", "حجر", "حناء", "حذاء", "حوض استحمام", "حقيبة سفر", "حبر", "حفاضات", "حفار", "حنفية", "حصان خشبي"],
        'خ': ["خاتم", "خزانة", "خريطة", "خيط", "خلخال", "خشبة", "خيمة", "خنجر", "خرز", "خرطوم", "خلاط", "خردة", "خزان مياه", "خوذة", "خلائط", "خشب"],
        'د': ["درج", "دولاب", "دفتر", "دراجة", "دلو", "درع", "دباسة", "دهان", "دخان", "دراجة نارية", "ديزل", "دريل", "دش", "دايرة", "دبوس", "ديكور"],
        'ذ': ["ذهب", "ذراع", "ذيل", "ذرة", "ذاكرة", "ذباب", "ذراع قيادة", "ذبيحة"],
        'ر': ["راديو", "رسالة", "رمان", "رمح", "رف", "رصاص", "رسام", "رواق", "روضة", "ركن", "راية", "رباط", "رمال", "ريشة", "رافعة", "رصيف", "راديد"],
        'ز': ["زجاجة", "زيت", "زر", "زهرية", "زمرد", "زنان", "زلاجة", "زورق", "زاوية", "زيوت", "زليج", "زاوية حائط"],
        'س': ["سجادة", "سيارة", "سرير", "ساعة", "سيف", "سكين", "سلك", "سبورة", "ستارة", "سلسلة", "سفينة", "سطل", "سلاح", "سقف", "سدادة", "سجائر", "سماعة"],
        'ش': ["شباك", "شارع", "شاشة", "شمعدان", "شوكة", "شاحن", "شمسية", "شاكوش", "شبكة", "شريط", "شوكولاتة", "شمعة", "شراب", "شاحنة", "شنطة", "شباك حديد"],
        'ص': ["صندوق", "صواني", "صاروخ", "صنبور", "صخرة", "صورة", "صنوبر", "صقر", "صابون", "صينية", "صنبور مياه", "صوف", "صاروخ حربي", "صامولة", "صنارة", "صواريخ"],
        'ض': ["ضوء", "طرد", "ضرس", "ضباب", "ضفيرة", "ضمان", "ضوء كاشف", "ضابطة"],
        'ط': ["طاولة", "طائرة", "طوب", "طبلة", "طوق", "طفاية", "طاقية", "طبلون", "طين", "طاحونة", "طرحة", "طرد بريدي", "طقم", "طوب طمي"],
        'ظ': ["ظرف", "ظلال", "ظفر", "ظلال شجرة", "ظرف نامه"],
        'ع': ["عقد", "عصا", "علم", "عربة", "عمود", "عطر", "عربة نقل", "عجلة", "عصارة", "علبة", "عازل", "عصا مشي", "عتبة", "عنقود", "عدسة"],
        'غ': ["غسالة", "غطاء", "غرفة", "غسول", "غلاية", "غواصة", "غربال", "غاز", "غراء", "غمد", "غرزة", "غلاف كتاب", "غضروف"],
        'ف': ["فانوس", "فرن", "فنجان", "فأس", "فستان", "فرشاة", "فراش", "فوطة", "فلاشة", "فحم", "فازة", "فرامل", "فخار", "فولتامتر", "فولاذ"],
        'ق': ["قلم", "قفل", "قدر", "قماش", "قطار", "قارب", "قلم رصاص", "قلادة", "قبر", "قمامة", "قصر", "قبعة", "قوس", "قنابل", "قناة", "قارب مطاطي"],
        'ك': ["كرسي", "كتاب", "كوب", "كتالوج", "كمبيوتر", "كيس", "كراسة", "كيس بلاستيك", "كبسولة", "كشاف", "كمامة", "كاسيت", "كيبورد", "كاميرا", "كرتونة", "كوتشي"],
        'ل': ["لعبة", "لمبة", "لحاف", "لجام", "لوحة", "لصق", "لجام حصان", "لؤلؤ", "لوح خشبي", "لاستيك", "لبادة", "لوازم"],
        'م': ["مكتب", "مفتاح", "مقص", "مرآة", "مروحة", "مطرقة", "منشفة", "مصباح", "مسدس", "مسمار", "منضدة", "مقياس", "محفظة", "مسطرة", "مظلة", "مخدة", "ملعقة"],
        'ن': ["نجفة", "نظارة", "نهر", "وسادة", "نرد", "ناموسية", "ناظور", "نحاس", "نشافة", "نقطة ماء", "نوتة", "نسخة", "نول حياكة"],
        'ه': ["هاتف", "هرم", "هودج", "هليكوبتر", "هواية", "هيكل", "هون", "هاند فري", "هدايا", "هوانم"],
        'و': ["ورقة", "وسام", "وعاء", "وسادة", "وسيلة", "وساطة", "وشاح", "وردة صناعية", "وحدة تخزين", "واقي شاشة"],
        'ي': ["يد", "يخوت", "يمامة", "يقطين", "يود", "يبرق", "يكتشف", "ينبوع معدني"]
    },
    "حيوان": {
        'ا': ["اسد", "ارنب", "اتان", "افعى", "اخطبوط", "ابل", "اتان", "ابو بريص", "ابو منجل", "اسد البحر", "اغنام", "اوركا", "اسكارب", "ارنب وحشي"],
        'ب': ["بطة", "بقرة", "بومة", "باز", "ببر", "بلبل", "ببغاء", "بطريق", "باعوض", "بقر", "ببر سيبيري", "بومة حظيرة", "بلشون", "بزاق", "برمائيات"],
        'ت': ["تمساح", "ترس", "تيس", "تنين", "تنين كومودو", "ترسة", "تتويج", "تيس منزلي", "تفاخ"],
        'ث': ["ثعلب", "ثور", "ثعبان", "ثعلب قطبي", "ثعبان النمر", "ثور وحشي", "ثدييات"],
        'ج': ["جمل", "جاموس", "جرو", "جراد", "جمل عربي", "جربوع", "جوارح", "جندب", "جعران", "جاموس البرك", "جواثم"],
        'ح': ["حصان", "حمار", "حوت", "حمام", "حرباء", "حمار وحشي", "حوت أزرق", "حلزون", "حوت قاتل", "حصان البحر", "حشرات", "حيوان منقرض", "حجل", "حرباء نمرية"],
        'خ': ["خروف", "خنزير", "خلد", "خرتيت", "خطاف", "خنزير بري", "خفاش", "خلد الماء", "خنزير غينيا", "خفس", "خيل", "خنافس"],
        'د': ["دب", "دجاجة", "دولفين", "ديك", "ضفدع", "دود", "دب قطبي", "ديك رومي", "دودة الأرض", "دلفين", "دود القز", "دحروش", "دب الباندا"],
        'ذ': ["ذئب", "ذباب", "ذئاب", "ذباب الفاكهة", "ذئب رمادي", "ذباب الخيل", "ذراع طويل"],
        'ر': ["راكون", "رافل", "روبيان", "رنة", "رياح", "روبوت حيواني", "رعاش", "رفراف", "روبيان الماء العذب"],
        'ز': ["زرافة", "زنبور", "زبابة", "زواحف", "زرافة الأبقار", "زبابة الشجر", "زقزاق", "زغابة"],
        'س': ["سلحفاة", "سنجاب", "سمكة", "سبع", "سرطان", "سحلية", "سنجاب طائر", "سمك القرش", "سرطان البحر", "سيد قشطة", "سلوقي", "سرعوف", "سُمّان"],
        'ش': ["شاهين", "شيمبانزي", "شبوط", "شامبانزي", "شرغوف", "شبنم", "شصي", "شيهم", "شيبان"],
        'ص': ["صقر", "صيصان", "صعوة", "صقر الجريت", "صيصان الدجاج", "صقر حر", "صلال", "صرد"],
        'ض': ["ضفدع", "ضبع", "ضب", "ضفدع شجري", "ضبع رقطاء", "ضب عربي", "ضفدع مائي", "ضفدع الشجر"],
        'ط': ["طاووس", "طائر", "طيطوي", "طائر السمنة", "طائر النحام", "طائر الدودو", "طائر الطنان", "طيطوي الأنقاض"],
        'ظ': ["ظبي", "ظربان", "ظبي الأفريقي", "ظبي الريم", "ظربان مخطط", "ظبي التبت"],
        'ع': ["عصفور", "عقرب", "عنزة", "عجل", "عنكبوت", "عصفور الجنة", "عقرب أصفر", "عنكبوت الأرملة السوداء", "عجل البقرة", "عنكبوت ذئبي", "عقاب"],
        'غ': ["غزال", "غراب", "غوريلا", "غرير", "غزال الصحراء", "غراب أسود", "غوريلا الجبل", "غرير العسل", "غزلان"],
        'ف': ["فيل", "فأر", "فهد", "فراشة", "فقمة", "فيل أفريقي", "فهد منقط", "فراشة الملك", "فقمة الفراء", "فأر الحقل", "فئران"],
        'ق': ["قرد", "قط", "قنفذ", "قندس", "قرش", "قرد البابون", "قط سيامي", "قنفذ بري", "قندس النهر", "قرش أبيض", "قمري", "قمل"],
        'ك': ["كلب", "كنغر", "كوالا", "كلب بوليسي", "كنغر رمادي", "كوالا أسترالي", "كاسوري", "كباش", "كبش", "كلب البحر"],
        'ل': ["ليمور", "لاما", "لؤلؤة البحر", "ليمور طائر", "لجأة بحرية", "ليوبارد", "لواحم"],
        'م': ["ماعز", "معز", "ماموث", "مهر", "مها", "محار", "مرجان", "مكاو", "نسناس", "معز جبلي", "ماعز أبيض"],
        'ن': ["نمر", "نسر", "ناقة", "نعامة", "نحلة", "نورس", "نمر عربي", "نسر أصلع", "نعامة أفريقية", "نحلة العسل", "نورس سمك", "ناقة عربية", "نمس"],
        'ه': ["هدهد", "هامستر", "هراس", "هدهد سليمان", "هامستر ذهبي", "هيبو", "هيدرا", "هوام"],
        'و': ["وعل", "ورل", "وطواط", "وعل جبلي", "ورل صحراوي", "وطواط مصاص دماء", "وعل جبال الألب"],
        'ي': ["يمامة", "يعسوب", "يربوع", "يمامة محزومة", "يعسوب أحمر", "يربوع الصحراء", "يعسوب مائي"]
    },
    "نبات": {
        'ا': ["اناناس", "ازهار", "ارز", "انجاص", "افوكادو", "التوت", "اسبرجس", "اشجار", "المانجو", "اوراق الشجر", "الخس", "البصل", "الثوم"],
        'ب': ["برتقال", "بصل", "بطاطس", "بامية", "بقدونس", "بروكلي", "بابايا", "بصل سبز", "بطاطا", "بليلة", "بقوليات", "بنسي", "بكرات"],
        'ت': ["تفاح", "تمر", "تين", "ترمس", "توليب", "تمر هندي", "توت شامي", "توت البري", "تيفه", "تيريزا", "توابل"],
        'ث': ["ثوم", "ثمر", "ثوم بري", "ثمام", "ثعلبية", "ثيام", "ثمر النخيل"],
        'ج': ["جزر", "جوز", "جوافة", "جرجير", "زنجبيل", "جوز الهند", "جوزة الطيب", "جزر بستاني", "جلوبار", "جريب فروت", "جريس"],
        'ح': ["حلبة", "حمص", "حناء", "حبق", "حشيش", "حبة البركة", "حنتيت", "حارث", "حرمل", "حسک", "حلفا"],
        'خ': ["خيار", "خس", "خوخ", "خردل", "خطمي", "خبيزة", "خس لولبي", "خوخ مجفف", "خيزران", "خشخاش", "خرفيش"],
        'د': ["دراق", "دخن", "داتورا", "دبيق", "دارصيني", "دبق", "دوم", "دباء", "داليا"],
        'ذ': ["ذرة", "ذرة صفراء", "ذرة بيضاء", "ذرق", "ذباب النبتة"],
        'ر': ["رمان", "ريحان", "روزماري", "راوند", "رشاد", "رمان أسود", "ريحان بري", "راع الهنود"],
        'ز': ["زيتون", "زعتر", "زعفران", "زنبق", "زهرة", "زنجبيل", "زيتون أخضر", "زهر الليمون", "زهرة الشمس", "زريعة"],
        'س': ["سبانخ", "سمسم", "سنوبر", "سريس", "سذاب", "سوسن", "سنديان", "سذاب بري", "سذاب أصفر", "سلطة نباتية"],
        'ش': ["شعير", "شمندر", "شيح", "شبت", "شمام", "شوكولاتة نباتية", "شبت أخضر", "شوح", "شجيرات", "شذاب"],
        'ص': ["صبار", "صندل", "صبار تين الشوغي", "صندل أحمر", "صفيراء", "صبر حقيقي"],
        'ض': ["ضريع", "ضرم", "ضفاضع النبات", "ضريع البحر"],
        'ط': ["طماطم", "طحلب", "طلح", "طماطم كرزية", "طحالب بحرية", "طرفة", "طيطان"],
        'ظ': ["ظيان", "ظفرة", "ظيان أسود", "ظلة"],
        'ع': ["عنب", "عدس", "عناب", "عفص", "عرقسوس", "عنب الديب", "علس", "عرفج", "عشبة الليمون", "عصفور الشجر"],
        'غ': ["غار", "غاب", "غرقد", "غار طائر", "غابن", "غرقد بري", "غدير النبات"],
        'ف': ["فراولة", "فاصوليا", "فجل", "فلفل", "فول", "فستق", "فلفل حار", "فطر", "فجل أحمر", "فول سوداني", "فانيليا", "فربيون"],
        'ق': ["قرفة", "قرع", "قرنفل", "قصب", "قطن", "قمح", "قصب السكر", "قرع العسل", "قرنبيط", "قنب", "قطن طبيعي"],
        'ك': ["كمثرى", "كوسة", "كمون", "كرز", "كرنب", "كنتالوب", "كرفس", "كزبرة", "كركديه", "كستناء", "كوسا", "كافور"],
        'ل': ["ليمون", "لوبيا", "لافاندر", "لبلاب", "ليمون أصفر", "لوبيا سبز", "لوز", "لفت", "ليفة", "لسان الثور"],
        'م': ["موز", "مانجو", "ملوخية", "نعناع", "مشمش", "ميرمية", "موز بري", "ماندارين", "مرمية", "محلب", "ميرامية"],
        'ن': ["نعناع", "نرجس", "نسرين", "نخيل", "نرجس بري", "نفل", "نسرين وردي", "نيم", "نباتات زينة"],
        'ه': ["هليون", "هيل", "هندباء", "هليون أبيض", "هيل أخضر", "هندباء برية", "هودج النبات"],
        'و': ["ورد", "ورد جوري", "ورق غار", "ورق عنب", "ورد بلدي", "ورق التوت"],
        'ي': ["يوسفي", "ياسمين", "يقطين", "يوسفي صيني", "ياسمين أبيض", "يمام نباتي"]
    },
    "بلاد": {
        'ا': ["اردن", "امريكا", "اسبانيا", "المانيا", "ايطاليا", "امارات", "ايران", "استراليا", "ارجنتين", "افغانستان", "اسكتلندا", "ايرلندا", "البانيا", "اكرانيا", "اثيوبيا"],
        'ب': ["بريطانيا", "برازيل", "بلجيكا", "بحرين", "بلغاريا", "بيلاروسيا", "بنما", "باراغواي", "بنغلاديش", "بروناي", "بولندا", "بوسنة والهرسك"],
        'ت': ["تركيا", "تونس", "تشاد", "تايوان", "تشيلي", "تايلاند", "تنزانيا", "تركمانستان", "تيمور الشرقية", "توجو"],
        'ث': ["ثيودسيا", "ثقيف", "ثمود", "ثياسيل", "ثيساليا"],
        'ج': ["جزائر", "يابان", "جيبوتي", "جامايكا", "جورجيا", "جزر القمر", "جزر البهاما", "جزر المالديف", "جزر سليمان", "جيرسي"],
        'ح': ["حبشة", "حائر", "حرمة", "حيفا", "حمص"],
        'خ': ["خليج", "خنشلة", "خراسان", "خارجية"],
        'د': ["دانمارك", "دبي", "دوحة", "dominica", "جمهورية الدومينيكان", "دكا"],
        'ذ': ["ذمار", "ذراع الموت"],
        'ر': ["روسيا", "رومانيا", "رواندا", "رأس الخيمة", "ريال", "رأس الجبل"],
        'ز': ["زيمبابوي", "زامبيا", "زغرب", "زليتن", "زحلة"],
        'س': ["سعودية", "سودان", "سوريا", "سويسرا", "سنغال", "سنغافورة", "سويد", "سلوفاكيا", "سلوفينيا", "سريلانكا", "سيراليون", "صومال", "صربيا"],
        'ش': ["صين", "شيلي", "شيشان", "شارقة", "شام"],
        'ص': ["صومال", "صربيا", "صين", "صعيد مصر", "صلالة"],
        'ض': ["ضفة الغربية", "ضالع", "ضبا"],
        'ط': ["طاجيكستان", "طنجة", "طهران", "طرابلس", "طليطلة", "طبريا"],
        'ظ': ["ظفار", "ظهران", "ظفر"],
        'ع': ["عراق", "عمان", "عجمان", "عقبة", "عمورية", "عنبورة"],
        'غ': ["غانا", "غواتيمالا", "غينيا", "غابون", "غزة", "غرناطة", "غوادالاخارا"],
        'ف': ["فرنسا", "فلسطين", "فلبين", "فنلندا", "فنزويلا", "فيتنام", "فاتيكان", "فيجي", "فاروقية"],
        'ق': ["قطر", "قبرص", "قيرغيزستان", "قاهرة", "قيروان", "قسنطينة", "قازاقستان", "القوصرة"],
        'ك': ["كويت", "كندا", "كولومبيا", "كوبا", "كينيا", "كاميرون", "كرواتيا", "كمبوديا", "كوريا الجنوبية", "كوريا الشمالية", "كازاخستان"],
        'ل': ["لبنان", "ليبيا", "لوكسمبورغ", "ليتوانيا", "لاتفيا", "ليبيريا", "ليختنشتاين", "لندن", "لشبونة", "لوس أنجلوس"],
        'م': ["مصر", "مغرب", "موريتانيا", "ماليزيا", "المكسيك", "مالي", "مدغشقر", "مالطا", "مقدونيا", "موريشيوس", "ميانمار", "موزمبيق"],
        'ن': ["نرويج", "نمسا", "نيبال", "نيجيريا", "نيوزيلندا", "نيجر", "نيكاراغوا", "ناورو", "نيويورك"],
        'ه': ["هند", "هولندا", "هونج كونج", "هنغاريا", "هندوراس", "هايتي", "هارلم"],
        'و': ["ويلز", "واتيكان", "وهران", "واشنطن", "وساطة"],
        'ي': ["يمن", "يابان", "يونان", "يوغسلافيا", "يسرى", "يريفان"]
    }
}

def normalize_arabic(text):
    text = text.strip()
    replacements = {'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ى': 'ي', 'ة': 'ه'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def check_word_validity(word: str, category: str, letter: str) -> bool:
    clean_word = normalize_arabic(word)
    clean_letter = normalize_arabic(letter)
    if not clean_word.startswith(clean_letter):
        return False
    cat_dict = VALID_BUS_WORDS.get(category, {})
    possible_words = cat_dict.get(letter, [])
    normalized_db_words = [normalize_arabic(w) for w in possible_words]
    return clean_word in normalized_db_words

@bot.event
async def on_ready():
    try:
        guild_id = 1527415229279895744
        guild = discord.Object(id=guild_id)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        print(f"Bot online | Synced {len(synced)} commands to guild {guild_id}.")
    except Exception as e:
        print(f"Sync error: {e}")

async def start_bus_timer(cid, channel):
    await asyncio.sleep(60)
    game = bus_games.get(cid)
    if game and game.get("started", False):
        bus_games.pop(cid, None)
        try:
            await channel.send(embed=games.embed("انتهت اللعبة", "تم إيقاف أتوبيس كومبليت لعدم وجود تفاعل أو إجابات خلال دقيقة واحدة.", 0xFF0000))
        except:
            pass

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    cid = message.channel.id
    if cid in bus_games:
        g_data = bus_games[cid]
        if g_data.get("started", False) and message.author.id in g_data["players"]:
            content = message.content.strip()
            if not content:
                return
            
            is_valid = check_word_validity(content, g_data["category"], g_data["letter"])

            if is_valid:
                n_letter, n_cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
                bus_games[cid].update({"letter": n_letter, "category": n_cat})
                
                if "timer_task" in g_data and g_data["timer_task"]:
                    g_data["timer_task"].cancel()
                
                new_task = asyncio.create_task(start_bus_timer(cid, message.channel))
                bus_games[cid]["timer_task"] = new_task

                await message.reply(
                    embed=games.embed("إجابة صحيحة", f"أحسنت {message.author.mention}! الكلمة (**{message.content}**) صحيحة.\n\nالمطلوب الجديد: **{n_cat}** بحرف **{n_letter}**\n(لديك دقيقة واحدة للإجابة أو التخطي)", config.COLORS["success"]),
                    view=BusGameActiveView(cid)
                )
                return
            else:
                await message.reply("إجابتك غلط")

    await bot.process_commands(message)

@bot.tree.command(name="stop", description="إيقاف أي لعبة جارية في هذه الروم")
async def stop_cmd(interaction: discord.Interaction):
    cid = interaction.channel_id
    stopped_any = False
    
    if cid in bus_games:
        if "timer_task" in bus_games[cid] and bus_games[cid]["timer_task"]:
            bus_games[cid]["timer_task"].cancel()
        bus_games.pop(cid, None)
        stopped_any = True
        
    if roulette_games.pop(cid, None): stopped_any = True
    if mafia_games.pop(cid, None): stopped_any = True
    if chairs_games.pop(cid, None): stopped_any = True
    
    if stopped_any:
        await interaction.response.send_message(embed=games.embed("تم إيقاف اللعبة", f"تم إنهاء جميع الألعاب النشطة في هذه الروم بواسطة {interaction.user.mention}", 0xFF0000))
    else:
        await interaction.response.send_message("لا توجد أي لعبة تعمل حالياً في هذه الروم لإيقافها.", ephemeral=True)

GAME_CHOICES = [
    discord.app_commands.Choice(name="Roulette", value="roulette"),
    discord.app_commands.Choice(name="Mafia", value="mafia"),
    discord.app_commands.Choice(name="Guess Country", value="country"),
    discord.app_commands.Choice(name="Hide and Seek", value="hide"),
    discord.app_commands.Choice(name="Musical Chairs", value="chairs"),
    discord.app_commands.Choice(name="Dice Roll", value="dice"),
    discord.app_commands.Choice(name="Replica", value="replica"),
    discord.app_commands.Choice(name="Rock Paper Scissors", value="rps"),
    discord.app_commands.Choice(name="XO", value="xo"),
    discord.app_commands.Choice(name="Hot XO", value="hotxo"),
    discord.app_commands.Choice(name="Bus Complete", value="bus"),
    discord.app_commands.Choice(name="Bank Game", value="bank")
]

@bot.tree.command(name="game", description="Start a new game")
@discord.app_commands.choices(choice=GAME_CHOICES)
async def game_cmd(interaction: discord.Interaction, choice: discord.app_commands.Choice[str]):
    try:
        g, p, cid = choice.value, interaction.user, interaction.channel_id
        if g == "roulette":
            if cid in roulette_games: return await interaction.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
            roulette_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            view = RouletteLobbyView(cid)
            await interaction.response.send_message(embed=games.embed("لعبة الروليت", f"المنشئ: {p.mention}\nاللاعبون: 1\n\nيجب أن يكون هناك لاعبان على الأقل لتبدأ العجلة! اضغط للانضمام خلال 20 ثانية"), view=view)
            asyncio.create_task(run_roulette_timer(cid, interaction.channel, await interaction.original_response(), view))
            return
        if g == "dice":
            res, wins = games.roll_dice([p.display_name, "البوت"])
            return await interaction.response.send_message(embed=games.embed("رمي النرد", f"\n".join(f"**{k}**: `{v}`" for k, v in res.items()) + f"\n\nالفائز: {', '.join(wins)}", config.COLORS["success"]))
        if g == "mafia":
            if cid in mafia_games: return await interaction.response.send_message("توجد لعبة مافيا تعمل بالفعل.", ephemeral=True)
            mafia_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False}
            return await interaction.response.send_message(embed=games.embed("لعبة المافيا", f"المنشئ: {p.mention}\nالحد الأدنى: 4 لاعبين"), view=MafiaView(cid))
        if g == "country":
            c = games.random_country()
            return await interaction.response.send_message(embed=games.embed("احزر الدولة", f"ما هي الدولة التي يتبعها هذا العلم؟\n\n{c['flag']}"), view=CountryView(c))
        if g == "hide":
            seeker, hidden = games.hide_and_seek([p.display_name, "اللاعب 2", "اللاعب 3", "اللاعب 4"])
            return await interaction.response.send_message(embed=games.embed("لعبة الاختباء", f"الباحث: {seeker}\nالمختبئون:\n" + "".join(f"- {x}\n" for x in hidden)))
        if g == "chairs":
            if cid in chairs_games: return await interaction.response.send_message("لعبة الكراسي تعمل بالفعل.", ephemeral=True)
            chairs_games[cid] = {"host": p.id, "players": {p.id: p}, "started": False, "round": 0}
            return await interaction.response.send_message(embed=games.embed("الكراسي", f"المنشئ: {p.mention}"), view=ChairsLobbyView(cid))
        if g == "replica":
            return await interaction.response.send_message(embed=games.embed("لعبة النسخة", f"الشخصية المختارة:\n{games.replica([p.display_name, 'اللاعب 2', 'اللاعب 3'])}"))
        if g == "rps":
            return await interaction.response.send_message(embed=games.embed("حجر ورقة مقص", "اختر حركتك:"), view=RPSView())
        if g in ("xo", "hotxo"):
            return await interaction.response.send_message(embed=games.embed("لعبة إكس أو", "الدور على: X"), view=XoView())
        if g == "bus":
            if cid in bus_games: return await interaction.response.send_message("أتوبيس كومبليت يعمل بالفعل.", ephemeral=True)
            letter, cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
            bus_games[cid] = {
                "letter": letter, 
                "category": cat, 
                "host": p.id, 
                "players": [p.id], 
                "started": False,
                "timer_task": None
            }
            return await interaction.response.send_message(
                embed=games.embed("تجهيز أتوبيس كومبليت", f"أنشأ {p.mention} لعبة جديدة!\n\nاضغط على زر انضمام للمشاركة، وعند الانتهاء اضغط بدء اللعبة"), 
                view=BusLobbyView(cid, p.id)
            )
        
        await interaction.response.send_message(embed=games.embed("تنبيه", "هذه اللعبة غير متوفرة حالياً."), ephemeral=True)
    except Exception as e:
        print(f"Error in game_cmd: {e}")
        if not interaction.response.is_done():
            await interaction.response.send_message("حدث خطأ أثناء تشغيل اللعبة.", ephemeral=True)

class BusLobbyView(discord.ui.View):
    def __init__(self, cid, host_id):
        super().__init__(timeout=120)
        self.cid, self.host_id = cid, host_id

    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or game["started"]:
            return await i.response.send_message("انتهت اللعبة أو بدأت بالفعل.", ephemeral=True)
        if i.user.id in game["players"]:
            return await i.response.send_message("أنت منضم بالفعل!", ephemeral=True)
        
        game["players"].append(i.user.id)
        await i.response.send_message(f"انضم {i.user.mention} إلى أتوبيس كومبليت!", ephemeral=False)

    @discord.ui.button(label="بدء اللعبة", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        if i.user.id != self.host_id:
            return await i.response.send_message("فقط منشئ اللعبة يستطيع البدء!", ephemeral=True)
        game = bus_games.get(self.cid)
        if not game:
            return await i.response.send_message("اللعبة غير موجودة.", ephemeral=True)
        
        game["started"] = True
        
        timer_task = asyncio.create_task(start_bus_timer(self.cid, i.channel))
        game["timer_task"] = timer_task

        await i.response.edit_message(
            embed=games.embed(
                "أتوبيس كومبليت",
                f"اللاعبون المشاركون: {len(game['players'])}\n\nالمطلوب للجميع: **{game['category']}** بحرف **{game['letter']}**\n\nأكتب الإجابة في الشات ليعرف عليها البوت تلقائياً!\n(لديك دقيقة واحدة للإجابة أو التخطي)"
            ),
            view=BusGameActiveView(self.cid)
        )

class BusGameActiveView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=None)
        self.cid = cid

    @discord.ui.button(label="انضمام للعبة", style=discord.ButtonStyle.success)
    async def join_active(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or not game["started"]:
            return await i.response.send_message("اللعبة غير نشطة.", ephemeral=True)
        if i.user.id in game["players"]:
            return await i.response.send_message("أنت منضم بالفعل لهذه اللعبة!", ephemeral=True)
        
        game["players"].append(i.user.id)
        await i.response.send_message(f"انضم {i.user.mention} إلى اللعبة بنجاح!", ephemeral=False)

    @discord.ui.button(label="تخطي السؤال", style=discord.ButtonStyle.secondary)
    async def skip_question(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if not game or not game["started"]:
            return await i.response.send_message("اللعبة غير نشطة.", ephemeral=True)
        
        n_letter, n_cat = random.choice(ARABIC_LETTERS), random.choice(BUS_CATEGORIES)
        game.update({"letter": n_letter, "category": n_cat})

        if "timer_task" in game and game["timer_task"]:
            game["timer_task"].cancel()
        game["timer_task"] = asyncio.create_task(start_bus_timer(self.cid, i.channel))

        await i.response.edit_message(
            embed=games.embed(
                "تم تخطي السؤال",
                f"قام {i.user.mention} بتخطي السؤال!\n\nالمطلوب الجديد: **{n_cat}** بحرف **{n_letter}**\n(لديك دقيقة واحدة للإجابة أو التخطي)"
            ),
            view=self
        )

    @discord.ui.button(label="إيقاف اللعبة", style=discord.ButtonStyle.danger)
    async def stop_bus_active(self, i: discord.Interaction, b: discord.ui.Button):
        game = bus_games.get(self.cid)
        if game and "timer_task" in game and game["timer_task"]:
            game["timer_task"].cancel()
            
        if bus_games.pop(self.cid, None):
            await i.response.edit_message(embed=games.embed("تم إيقاف اللعبة", f"تم الإنهاء بواسطة {i.user.mention}", 0xFF0000), view=None)
        else:
            await i.response.send_message("اللعبة منتهية بالفعل.", ephemeral=True)

async def run_roulette_timer(cid, channel, msg, view):
    await asyncio.sleep(20)
    view.stop()
    game = roulette_games.pop(cid, None)
    if not game or not game["players"]: return
    
    players_list = list(game["players"].values())
    
    try: await msg.delete()
    except: pass

    if len(players_list) < 2:
        await channel.send(embed=games.embed("إلغاء الروليت", "تم إلغاء اللعبة لعدم اكتمال الحد الأدنى من اللاعبين (مطلوب لاعبان على الأقل)."))
        return

    players_data = []
    for usr in players_list:
        try: img = await games.download_avatar(usr.display_avatar.url)
        except: img = None
        players_data.append({"name": usr.display_name, "user": usr, "avatar": img})
    
    winner_name = games.roulette_winner([p["name"] for p in players_data])
    winner_user = next((p["user"] for p in players_data if p["name"] == winner_name), players_list[0])

    try:
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", "جارٍ التدوير..."), file=discord.File(games.create_roulette_gif(players_data, winner_name), filename="roulette.gif"))
    except:
        spin_msg = await channel.send(embed=games.embed("عجلة الروليت", f"الفائز: **{winner_name}**"))
    
    await asyncio.sleep(7)
    
    try: await spin_msg.delete()
    except: pass

    await channel.send(
        embed=games.embed("فائز الروليت", f"مبروك للفائز:\n{winner_user.mention}\n\nهل تريدون إعادة اللعبة؟", config.COLORS["success"]),
        view=RouletteRestartView()
    )

class RouletteRestartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(label="إعادة اللعبة", style=discord.ButtonStyle.success)
    async def restart(self, i: discord.Interaction, b: discord.ui.Button):
        cid = i.channel_id
        if cid in roulette_games:
            return await i.response.send_message("توجد لعبة روليت تعمل بالفعل.", ephemeral=True)
        
        roulette_games[cid] = {"host": i.user.id, "players": {i.user.id: i.user}, "started": False}
        view = RouletteLobbyView(cid)
        
        await i.response.edit_message(embed=games.embed("لعبة الروليت", f"تم إعادة فتح اللعبة بواسطة {i.user.mention}\nاللاعبون: 1\n\nيجب أن يكون هناك لاعبان على الأقل لتبدأ العجلة! اضغط للانضمام خلال 20 ثانية"), view=view)
        asyncio.create_task(run_roulette_timer(cid, i.channel, await i.original_response(), view))

    @discord.ui.button(label="إنهاء", style=discord.ButtonStyle.danger)
    async def stop_game(self, i: discord.Interaction, b: discord.ui.Button):
        await i.response.edit_message(embed=games.embed("انتهت اللعبة", "شكراً لكم على اللعب!"), view=None)

class RouletteLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=20)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = roulette_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]: return await i.response.send_message("لا يمكنك الانضمام.", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("لعبة الروليت", f"المنشئ: <@{game['host']}>\nاللاعبون: {len(game['players'])}\n\n(مطلوب لاعبان على الأقل لبدء الدوران)"))
        await i.followup.send("تم الانضمام!", ephemeral=True)

class MafiaView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or game["started"] or i.user.id in game["players"]: return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("لعبة المافيا", f"اللاعبون: {len(game['players'])}"))
    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = mafia_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 4: return await i.response.send_message("مطلوب 4 لاعبين كحد أدنى.", ephemeral=True)
        game["started"] = True
        roles = games.create_mafia_roles(list(game["players"].keys()))
        for uid, usr in game["players"].items():
            try: await usr.send(embed=games.embed("دورك في المافيا", f"دورك: **{roles.get(uid, 'مواطن')}**"))
            except: pass
        mafia_games.pop(self.cid, None)
        await i.response.edit_message(embed=games.embed("بدء المافيا", "تم إرسال الأدوار بالخاص."), view=None)

class ChairsLobbyView(discord.ui.View):
    def __init__(self, cid):
        super().__init__(timeout=300)
        self.cid = cid
    @discord.ui.button(label="انضمام", style=discord.ButtonStyle.success)
    async def join(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id in game["players"]: return await i.response.send_message("خطأ", ephemeral=True)
        game["players"][i.user.id] = i.user
        await i.response.edit_message(embed=games.embed("الكراسي", f"اللاعبون: {len(game['players'])}"))
    @discord.ui.button(label="بدء", style=discord.ButtonStyle.primary)
    async def start(self, i: discord.Interaction, b: discord.ui.Button):
        game = chairs_games.get(self.cid)
        if not game or i.user.id != game["host"] or len(game["players"]) < 2: return await i.response.send_message("مطلوب لاعبين اثنين على الأقل.", ephemeral=True)
        game["started"] = True
        await i.response.edit_message(embed=games.embed("الكراسي", "بدأت الموسيقى!"), view=None)
        asyncio.create_task(run_chairs(self.cid))

async def run_chairs(cid):
    game = chairs_games.get(cid)
    if not game: return
    players = list(game["players"].values())
    if len(players) == 1:
        chairs_games.pop(cid, None)
        ch = bot.get_channel(cid)
        if ch: await ch.send(embed=games.embed("فائز الكراسي", f"{players[0].display_name}", config.COLORS["success"]))
        return
    game["round"] += 1
    view = ChairView(cid, len(players) - 1)
    ch = bot.get_channel(cid)
    if ch: await ch.send(embed=games.embed(f"الجولة {game['round']}", "اضغط بسرعة على الكرسي!"), view=view)
    await asyncio.sleep(4)
    view.stop()
    loser = next((p for p in players if p.id not in view.taken), None)
    if loser and loser.id in game["players"]:
        del game["players"][loser.id]
        if ch: await ch.send(embed=games.embed("استبعاد", f"تم استبعاد: {loser.display_name}"))
    await asyncio.sleep(2)
    asyncio.create_task(run_chairs(cid))

class ChairView(discord.ui.View):
    def __init__(self, cid, count):
        super().__init__(timeout=4)
        self.taken = set()
        for idx in range(count):
            btn = discord.ui.Button(label=f"كرسي {idx+1}", style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, b=btn):
                game = chairs_games.get(cid)
                if not game or i.user.id not in game["players"] or i.user.id in self.taken: return await i.response.send_message("غير مسموح", ephemeral=True)
                self.taken.add(i.user.id)
                b.disabled = True
                await i.response.send_message("جلست على كرسي!", ephemeral=True)
                try: await i.message.edit(view=self)
                except: pass
            btn.callback = cb
            self.add_item(btn)

class XoButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="-", row=x)
    async def callback(self, i: discord.Interaction):
        if self.label != "-": return await i.response.send_message("مأخوذة!", ephemeral=True)
        self.label, self.style = "X", discord.ButtonStyle.danger
        await i.response.edit_message(view=self.view)

class XoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        for x in range(3):
            for y in range(3): self.add_item(XoButton(x, y))

class CountryView(discord.ui.View):
    def __init__(self, data):
        super().__init__(timeout=30)
        for choice in data["choices"]:
            btn = discord.ui.Button(label=choice, style=discord.ButtonStyle.secondary)
            async def cb(i: discord.Interaction, ch=choice):
                res = "إجابة صحيحة" if ch == data["answer"] else "إجابة خاطئة"
                await i.response.edit_message(embed=games.embed(res, f"الإجابة الصحيحة: {data['answer']}"), view=None)
            btn.callback = cb
            self.add_item(btn)

class RPSView(discord.ui.View):
    def __init__(self, cid=None):
        super().__init__(timeout=30)
        for c in [("حجر", "Rock"), ("ورقة", "Paper"), ("مقص", "Scissors")]:
            btn = discord.ui.Button(label=c[0], style=discord.ButtonStyle.primary)
            async def cb(i: discord.Interaction, choice=c[1]):
                bot_c = random.choice(["Rock", "Paper", "Scissors"])
                wins = {"Rock": "Scissors", "Scissors": "Paper", "Paper": "Rock"}
                trans = {"Rock": "حجر", "Paper": "ورقة", "Scissors": "مقص"}
                res = "تعادل" if choice == bot_c else ("لقد فزت" if wins[choice] == bot_c else "فاز البوت")
                await i.response.edit_message(embed=games.embed("حجر ورقة مقص", f"أنت: {trans[choice]}\nالبوت: {trans[bot_c]}\n\n**{res}**"), view=None)
            btn.callback = cb
            self.add_item(btn)

bot.run(config.TOKEN)
