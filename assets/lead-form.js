/* ===== Lead form + modal v1.0 =====
   Shared client-side UI for IndexResearch lead forms.
   Delivery endpoint is configured separately in /assets/form-config.js. */
(function installIndexResearchLeadForms(){
  if(window.__INDEXRESEARCH_LEAD_FORM_INSTALLED__) return;
  window.__INDEXRESEARCH_LEAD_FORM_INSTALLED__ = true;

  const FORM_ENDPOINT = window.INDEXRESEARCH_FORM_ENDPOINT || '';
  const COUNTRIES_JSON = "[{\"name\":\"Afghanistan (افغانستان‎)\",\"mask\":\"+93-99-999-9999\",\"iso2\":\"af\",\"dial\":\"+93\"},{\"name\":\"Albania (Shqipëri)\",\"mask\":\"+355(999) 999-999\",\"iso2\":\"al\",\"dial\":\"+355\"},{\"name\":\"Algeria (الجزائر‎)\",\"mask\":\"+213-99-999-9999\",\"iso2\":\"dz\",\"dial\":\"+213\"},{\"name\":\"Andorra\",\"mask\":\"+376-999-999\",\"iso2\":\"ad\",\"dial\":\"+376\"},{\"name\":\"Angola\",\"mask\":\"+244(999) 999-999\",\"iso2\":\"ao\",\"dial\":\"+244\"},{\"name\":\"Armenia (Հայաստան)\",\"mask\":\"+374-99-999-999\",\"iso2\":\"am\",\"dial\":\"+374\"},{\"name\":\"Antigua and Barbuda\",\"mask\":\"+1 (268)999-9999\",\"iso2\":\"ag\",\"dial\":\"+1 (268)\"},{\"name\":\"Argentina\",\"mask\":\"+54(999) 9999-9999\",\"iso2\":\"ar\",\"dial\":\"+54\"},{\"name\":\"Australia\",\"mask\":\"+61-99-9999-9999\",\"iso2\":\"au\",\"dial\":\"+61\"},{\"name\":\"Austria (Österreich)\",\"mask\":\"+43(999) 999-99999\",\"iso2\":\"at\",\"dial\":\"+43\"},{\"name\":\"Azerbaijan (Azərbaycan)\",\"mask\":\"+994-99-999-99-99\",\"iso2\":\"az\",\"dial\":\"+994\"},{\"name\":\"Bahamas\",\"mask\":\"+1 (242)999-9999\",\"iso2\":\"bs\",\"dial\":\"+1 (242)\"},{\"name\":\"Bahrain (البحرين‎)\",\"mask\":\"+973-9999-9999\",\"iso2\":\"bh\",\"dial\":\"+973\"},{\"name\":\"Bangladesh (বাংলাদেশ)\",\"mask\":\"+880-9999-999999\",\"iso2\":\"bd\",\"dial\":\"+880\"},{\"name\":\"Barbados\",\"mask\":\"+1 (246)999-9999\",\"iso2\":\"bb\",\"dial\":\"+1 (246)\"},{\"name\":\"Belarus (Беларусь)\",\"mask\":\"+375(99) 999-99-99\",\"iso2\":\"by\",\"dial\":\"+375\"},{\"name\":\"Belgium (België)\",\"mask\":\"+32(999) 999-999\",\"iso2\":\"be\",\"dial\":\"+32\"},{\"name\":\"Belize\",\"mask\":\"+501-999-9999\",\"iso2\":\"bz\",\"dial\":\"+501\"},{\"name\":\"Benin (Bénin)\",\"mask\":\"+229-99-99-9999\",\"iso2\":\"bj\",\"dial\":\"+229\"},{\"name\":\"Bhutan (འབྲུག)\",\"mask\":\"+975-9-999-9999\",\"iso2\":\"bt\",\"dial\":\"+975\"},{\"name\":\"Bolivia\",\"mask\":\"+591-9-999-9999\",\"iso2\":\"bo\",\"dial\":\"+591\"},{\"name\":\"Bosnia and Herzegovina\",\"mask\":\"+387-99-999-999\",\"iso2\":\"ba\",\"dial\":\"+387\"},{\"name\":\"Botswana\",\"mask\":\"+267-99-999-999\",\"iso2\":\"bw\",\"dial\":\"+267\"},{\"name\":\"Brazil (Brasil)\",\"mask\":\"+55(99) 99999-9999\",\"iso2\":\"br\",\"dial\":\"+55\"},{\"name\":\"Brunei\",\"mask\":\"+673-999-9999\",\"iso2\":\"bn\",\"dial\":\"+673\"},{\"name\":\"Bulgaria (България)\",\"mask\":\"+359(999) 999-999\",\"iso2\":\"bg\",\"dial\":\"+359\"},{\"name\":\"Burkina Faso\",\"mask\":\"+226-99-99-9999\",\"iso2\":\"bf\",\"dial\":\"+226\"},{\"name\":\"Burundi (Uburundi)\",\"mask\":\"+257-99-99-9999\",\"iso2\":\"bi\",\"dial\":\"+257\"},{\"name\":\"Cambodia (កម្ពុជា)\",\"mask\":\"+855-99-999-999\",\"iso2\":\"kh\",\"dial\":\"+855\"},{\"name\":\"Cameroon (Cameroun)\",\"mask\":\"+237-9-99-99-99-99\",\"iso2\":\"cm\",\"dial\":\"+237\"},{\"name\":\"Canada\",\"mask\":\"+1(999) 999-9999\",\"iso2\":\"ca\",\"dial\":\"+1\"},{\"name\":\"Cape Verde (Kabu Verdi)\",\"mask\":\"+238(999) 99-99\",\"iso2\":\"cv\",\"dial\":\"+238\"},{\"name\":\"Central African Republic (République centrafricaine)\",\"mask\":\"+236-99-99-9999\",\"iso2\":\"cf\",\"dial\":\"+236\"},{\"name\":\"Chad (Tchad)\",\"mask\":\"+235-99-99-99-99\",\"iso2\":\"td\",\"dial\":\"+235\"},{\"name\":\"Chile\",\"mask\":\"+56-9-9999-9999\",\"iso2\":\"cl\",\"dial\":\"+56\"},{\"name\":\"China (中国)\",\"mask\":\"+86(999) 9999-9999\",\"iso2\":\"cn\",\"dial\":\"+86\"},{\"name\":\"Colombia\",\"mask\":\"+57(999) 999-9999\",\"iso2\":\"co\",\"dial\":\"+57\"},{\"name\":\"Comoros (جزر القمر‎)\",\"mask\":\"+269-99-99999\",\"iso2\":\"km\",\"dial\":\"+269\"},{\"name\":\"Congo (DRC) (Jamhuri ya Kidemokrasia ya Kongo)\",\"mask\":\"+243(999) 999-999\",\"iso2\":\"cd\",\"dial\":\"+243\"},{\"name\":\"Congo (Republic) (Congo-Brazzaville)\",\"mask\":\"+242-99-999-9999\",\"iso2\":\"cg\",\"dial\":\"+242\"},{\"name\":\"Cook Islands\",\"mask\":\"+682-99-999\",\"iso2\":\"ck\",\"dial\":\"+682\"},{\"name\":\"Costa Rica\",\"mask\":\"+506-9999-9999\",\"iso2\":\"cr\",\"dial\":\"+506\"},{\"name\":\"Cote d’Ivoire\",\"mask\":\"+225-99-999-999\",\"iso2\":\"ci\",\"dial\":\"+225\"},{\"name\":\"Croatia (Hrvatska)\",\"mask\":\"+385-99-999-9999\",\"iso2\":\"hr\",\"dial\":\"+385\"},{\"name\":\"Cuba\",\"mask\":\"+53-9-999-9999\",\"iso2\":\"cu\",\"dial\":\"+53\"},{\"name\":\"Cyprus (Κύπρος)\",\"mask\":\"+357-99-999-999\",\"iso2\":\"cy\",\"dial\":\"+357\"},{\"name\":\"Czech Republic (Česká republika)\",\"mask\":\"+420(999) 999-999\",\"iso2\":\"cz\",\"dial\":\"+420\"},{\"name\":\"Denmark (Danmark)\",\"mask\":\"+45-99-99-99-99\",\"iso2\":\"dk\",\"dial\":\"+45\"},{\"name\":\"Djibouti\",\"mask\":\"+253-99-99-99-99\",\"iso2\":\"dj\",\"dial\":\"+253\"},{\"name\":\"Dominica\",\"mask\":\"+1 (767)999-9999\",\"iso2\":\"dm\",\"dial\":\"+1 (767)\"},{\"name\":\"Dominican Republic (República Dominicana)\",\"mask\":\"+1(999) 999-9999\",\"iso2\":\"do\",\"dial\":\"+1\"},{\"name\":\"Ecuador\",\"mask\":\"+593-9-999-9999\",\"iso2\":\"ec\",\"dial\":\"+593\"},{\"name\":\"Egypt (مصر‎)\",\"mask\":\"+20(999) 999-9999\",\"iso2\":\"eg\",\"dial\":\"+20\"},{\"name\":\"El Salvador\",\"mask\":\"+503-99-99-9999\",\"iso2\":\"sv\",\"dial\":\"+503\"},{\"name\":\"Equatorial Guinea (Guinea Ecuatorial)\",\"mask\":\"+240-99-999-9999\",\"iso2\":\"gq\",\"dial\":\"+240\"},{\"name\":\"Eritrea\",\"mask\":\"+291-9-999-999\",\"iso2\":\"er\",\"dial\":\"+291\"},{\"name\":\"Estonia (Eesti)\",\"mask\":\"+372-9999-9999\",\"iso2\":\"ee\",\"dial\":\"+372\"},{\"name\":\"Ethiopia\",\"mask\":\"+251-99-999-9999\",\"iso2\":\"et\",\"dial\":\"+251\"},{\"name\":\"Fiji\",\"mask\":\"+679-999-9999\",\"iso2\":\"fj\",\"dial\":\"+679\"},{\"name\":\"Finland (Suomi)\",\"mask\":\"+358-999-9999999\",\"iso2\":\"fi\",\"dial\":\"+358\"},{\"name\":\"France\",\"mask\":\"+33(999) 999-999\",\"iso2\":\"fr\",\"dial\":\"+33\"},{\"name\":\"Gabon\",\"mask\":\"+241-9-99-99-99\",\"iso2\":\"ga\",\"dial\":\"+241\"},{\"name\":\"Gambia\",\"mask\":\"+220(999) 99-99\",\"iso2\":\"gm\",\"dial\":\"+220\"},{\"name\":\"Georgia (საქართველო)\",\"mask\":\"+995(999) 999-999\",\"iso2\":\"ge\",\"dial\":\"+995\"},{\"name\":\"Germany (Deutschland)\",\"mask\":\"+49(999) 999-99999\",\"iso2\":\"de\",\"dial\":\"+49\"},{\"name\":\"Ghana (Gaana)\",\"mask\":\"+233(999) 999-999\",\"iso2\":\"gh\",\"dial\":\"+233\"},{\"name\":\"Greece (Ελλάδα)\",\"mask\":\"+30(999) 999-9999\",\"iso2\":\"gr\",\"dial\":\"+30\"},{\"name\":\"Grenada\",\"mask\":\"+1 (473)999-9999\",\"iso2\":\"gd\",\"dial\":\"+1 (473)\"},{\"name\":\"Guatemala\",\"mask\":\"+502-9-999-9999\",\"iso2\":\"gt\",\"dial\":\"+502\"},{\"name\":\"Guinea (Guinée)\",\"mask\":\"+224-999-99-99-99\",\"iso2\":\"gn\",\"dial\":\"+224\"},{\"name\":\"Guinea-Bissau (Guiné Bissau)\",\"mask\":\"+245-9-999999\",\"iso2\":\"gw\",\"dial\":\"+245\"},{\"name\":\"Guyana\",\"mask\":\"+592-999-9999\",\"iso2\":\"gy\",\"dial\":\"+592\"},{\"name\":\"Haiti\",\"mask\":\"+509-99-99-9999\",\"iso2\":\"ht\",\"dial\":\"+509\"},{\"name\":\"Honduras\",\"mask\":\"+504-9999-9999\",\"iso2\":\"hn\",\"dial\":\"+504\"},{\"name\":\"Hong Kong (香港)\",\"mask\":\"+852-9999-9999\",\"iso2\":\"hk\",\"dial\":\"+852\"},{\"name\":\"Hungary (Magyarország)\",\"mask\":\"+36(999) 999-999\",\"iso2\":\"hu\",\"dial\":\"+36\"},{\"name\":\"Iceland (Ísland)\",\"mask\":\"+354-999-9999\",\"iso2\":\"is\",\"dial\":\"+354\"},{\"name\":\"India (भारत)\",\"mask\":\"+91(9999) 999-999\",\"iso2\":\"in\",\"dial\":\"+91\"},{\"name\":\"Indonesia\",\"mask\":\"+62(999) 999-99-999\",\"iso2\":\"id\",\"dial\":\"+62\"},{\"name\":\"Iran (ایران‎)\",\"mask\":\"+98(999) 999-9999\",\"iso2\":\"ir\",\"dial\":\"+98\"},{\"name\":\"Iraq (العراق‎)\",\"mask\":\"+964(999) 999-9999\",\"iso2\":\"iq\",\"dial\":\"+964\"},{\"name\":\"Ireland\",\"mask\":\"+353(999) 999-999\",\"iso2\":\"ie\",\"dial\":\"+353\"},{\"name\":\"Israel (ישראל‎)\",\"mask\":\"+972-999-999-9999\",\"iso2\":\"il\",\"dial\":\"+972\"},{\"name\":\"Italy (Italia)\",\"mask\":\"+39(999) 9999-999\",\"iso2\":\"it\",\"dial\":\"+39\"},{\"name\":\"Jamaica\",\"mask\":\"+1(999) 999-9999\",\"iso2\":\"jm\",\"dial\":\"+1\"},{\"name\":\"Japan (日本)\",\"mask\":\"+81-99-9999-9999\",\"iso2\":\"jp\",\"dial\":\"+81\"},{\"name\":\"Jordan (الأردن‎)\",\"mask\":\"+962-9-9999-9999\",\"iso2\":\"jo\",\"dial\":\"+962\"},{\"name\":\"Kazakhstan (Казахстан)\",\"mask\":\"+7(999) 999-99-99\",\"iso2\":\"kz\",\"dial\":\"+7\"},{\"name\":\"Kenya\",\"mask\":\"+254-999-999999\",\"iso2\":\"ke\",\"dial\":\"+254\"},{\"name\":\"Kiribati\",\"mask\":\"+686-99-999\",\"iso2\":\"ki\",\"dial\":\"+686\"},{\"name\":\"Kuwait (الكويت‎)\",\"mask\":\"+965-9999-9999\",\"iso2\":\"kw\",\"dial\":\"+965\"},{\"name\":\"Kyrgyzstan (Кыргызстан)\",\"mask\":\"+996(999) 999-999\",\"iso2\":\"kg\",\"dial\":\"+996\"},{\"name\":\"Laos (ລາວ)\",\"mask\":\"+856-99-999-999\",\"iso2\":\"la\",\"dial\":\"+856\"},{\"name\":\"Latvia (Latvija)\",\"mask\":\"+371-99-999-999\",\"iso2\":\"lv\",\"dial\":\"+371\"},{\"name\":\"Lebanon (لبنان‎)\",\"mask\":\"+961-99-999-999\",\"iso2\":\"lb\",\"dial\":\"+961\"},{\"name\":\"Lesotho\",\"mask\":\"+266-9-999-9999\",\"iso2\":\"ls\",\"dial\":\"+266\"},{\"name\":\"Liberia\",\"mask\":\"+231-99-999-9999\",\"iso2\":\"lr\",\"dial\":\"+231\"},{\"name\":\"Libya (ليبيا‎)\",\"mask\":\"+218-99-999-999\",\"iso2\":\"ly\",\"dial\":\"+218\"},{\"name\":\"Liechtenstein\",\"mask\":\"+423-999-99-99\",\"iso2\":\"li\",\"dial\":\"+423\"},{\"name\":\"Lithuania (Lietuva)\",\"mask\":\"+370(999) 99-999\",\"iso2\":\"lt\",\"dial\":\"+370\"},{\"name\":\"Luxembourg\",\"mask\":\"+352(999) 999-999\",\"iso2\":\"lu\",\"dial\":\"+352\"},{\"name\":\"Macao\",\"mask\":\"+853-9999-9999\",\"iso2\":\"mo\",\"dial\":\"+853\"},{\"name\":\"Macedonia (FYROM) (Македонија)\",\"mask\":\"+389-99-999-999\",\"iso2\":\"mk\",\"dial\":\"+389\"},{\"name\":\"Madagascar (Madagasikara)\",\"mask\":\"+261-99-99-99999\",\"iso2\":\"mg\",\"dial\":\"+261\"},{\"name\":\"Malawi\",\"mask\":\"+265-9-9999-9999\",\"iso2\":\"mw\",\"dial\":\"+265\"},{\"name\":\"Malaysia\",\"mask\":\"+60-99-999-9999\",\"iso2\":\"my\",\"dial\":\"+60\"},{\"name\":\"Maldives\",\"mask\":\"+960-999-9999\",\"iso2\":\"mv\",\"dial\":\"+960\"},{\"name\":\"Mali\",\"mask\":\"+223-99-99-9999\",\"iso2\":\"ml\",\"dial\":\"+223\"},{\"name\":\"Malta\",\"mask\":\"+356-9999-9999\",\"iso2\":\"mt\",\"dial\":\"+356\"},{\"name\":\"Marshall Islands\",\"mask\":\"+692-999-9999\",\"iso2\":\"mh\",\"dial\":\"+692\"},{\"name\":\"Mauritania (موريتانيا‎)\",\"mask\":\"+222-99-99-9999\",\"iso2\":\"mr\",\"dial\":\"+222\"},{\"name\":\"Mauritius (Moris)\",\"mask\":\"+230-999-9999\",\"iso2\":\"mu\",\"dial\":\"+230\"},{\"name\":\"Mexico (México)\",\"mask\":\"+52(999) 999-9999\",\"iso2\":\"mx\",\"dial\":\"+52\"},{\"name\":\"Mexico (México)\",\"mask\":\"+521(999) 999-9999\",\"iso2\":\"mb\",\"dial\":\"+521\"},{\"name\":\"Micronesia\",\"mask\":\"+691-999-9999\",\"iso2\":\"fm\",\"dial\":\"+691\"},{\"name\":\"Moldova (Republica Moldova)\",\"mask\":\"+373-9999-9999\",\"iso2\":\"md\",\"dial\":\"+373\"},{\"name\":\"Monaco\",\"mask\":\"+377-99-999-999\",\"iso2\":\"mc\",\"dial\":\"+377\"},{\"name\":\"Mongolia (Монгол)\",\"mask\":\"+976-99-99-9999\",\"iso2\":\"mn\",\"dial\":\"+976\"},{\"name\":\"Montenegro (Crna Gora)\",\"mask\":\"+382-99-999-999\",\"iso2\":\"me\",\"dial\":\"+382\"},{\"name\":\"Morocco (المغرب‎)\",\"mask\":\"+212-99-9999-999\",\"iso2\":\"ma\",\"dial\":\"+212\"},{\"name\":\"Mozambique (Moçambique)\",\"mask\":\"+258-99-999-999\",\"iso2\":\"mz\",\"dial\":\"+258\"},{\"name\":\"Myanmar (Burma) (မြန်မာ)\",\"mask\":\"+95-99-999-999\",\"iso2\":\"mm\",\"dial\":\"+95\"},{\"name\":\"Namibia (Namibië)\",\"mask\":\"+264-99-999-9999\",\"iso2\":\"na\",\"dial\":\"+264\"},{\"name\":\"Nauru\",\"mask\":\"+674-999-9999\",\"iso2\":\"nr\",\"dial\":\"+674\"},{\"name\":\"Nepal (नेपाल)\",\"mask\":\"+977-99-999-999\",\"iso2\":\"np\",\"dial\":\"+977\"},{\"name\":\"Netherlands (Nederland)\",\"mask\":\"+31-99-999-9999\",\"iso2\":\"nl\",\"dial\":\"+31\"},{\"name\":\"New Zealand\",\"mask\":\"+64(999) 999-999\",\"iso2\":\"nz\",\"dial\":\"+64\"},{\"name\":\"Nicaragua\",\"mask\":\"+505-9999-9999\",\"iso2\":\"ni\",\"dial\":\"+505\"},{\"name\":\"Niger (Nijar)\",\"mask\":\"+227-99-99-9999\",\"iso2\":\"ne\",\"dial\":\"+227\"},{\"name\":\"Nigeria\",\"mask\":\"+234-999-999-9999\",\"iso2\":\"ng\",\"dial\":\"+234\"},{\"name\":\"Niue\",\"mask\":\"+683-9999\",\"iso2\":\"nu\",\"dial\":\"+683\"},{\"name\":\"North Korea (조선 민주주의 인민 공화국)\",\"mask\":\"+850-99-999-999\",\"iso2\":\"kp\",\"dial\":\"+850\"},{\"name\":\"Norway (Norge)\",\"mask\":\"+47(999) 99-999\",\"iso2\":\"no\",\"dial\":\"+47\"},{\"name\":\"Oman (عُمان‎)\",\"mask\":\"+968-99-999-999\",\"iso2\":\"om\",\"dial\":\"+968\"},{\"name\":\"Panama\",\"mask\":\"+507 9999-9999\",\"iso2\":\"pa\",\"dial\":\"+507\"},{\"name\":\"Pakistan (پاکستان‎)\",\"mask\":\"+92(999) 999-9999\",\"iso2\":\"pk\",\"dial\":\"+92\"},{\"name\":\"Palau\",\"mask\":\"+680-999-9999\",\"iso2\":\"pw\",\"dial\":\"+680\"},{\"name\":\"Palestinian Territory\",\"mask\":\"+970 99 999 9999\",\"iso2\":\"ps\",\"dial\":\"+970\"},{\"name\":\"Papua New Guinea\",\"mask\":\"+675(999) 99-999\",\"iso2\":\"pg\",\"dial\":\"+675\"},{\"name\":\"Paraguay\",\"mask\":\"+595(999) 999-999\",\"iso2\":\"py\",\"dial\":\"+595\"},{\"name\":\"Peru (Perú)\",\"mask\":\"+51(999) 999-999\",\"iso2\":\"pe\",\"dial\":\"+51\"},{\"name\":\"Philippines\",\"mask\":\"+63(999) 999-9999\",\"iso2\":\"ph\",\"dial\":\"+63\"},{\"name\":\"Poland (Polska)\",\"mask\":\"+48(999) 999-999\",\"iso2\":\"pl\",\"dial\":\"+48\"},{\"name\":\"Portugal\",\"mask\":\"+351-99-999-9999\",\"iso2\":\"pt\",\"dial\":\"+351\"},{\"name\":\"Qatar (قطر‎)\",\"mask\":\"+974-9999-9999\",\"iso2\":\"qa\",\"dial\":\"+974\"},{\"name\":\"Romania (România)\",\"mask\":\"+40-99-999-9999\",\"iso2\":\"ro\",\"dial\":\"+40\"},{\"name\":\"Russian Federation (Российская Федерация)\",\"mask\":\"+7(999) 999-99-99\",\"iso2\":\"ru\",\"dial\":\"+7\"},{\"name\":\"Rwanda\",\"mask\":\"+250(999) 999-999\",\"iso2\":\"rw\",\"dial\":\"+250\"},{\"name\":\"Saint Kitts and Nevis\",\"mask\":\"+1 (869)999-9999\",\"iso2\":\"kn\",\"dial\":\"+1 (869)\"},{\"name\":\"Saint Lucia\",\"mask\":\"+1 (758)999-9999\",\"iso2\":\"lc\",\"dial\":\"+1 (758)\"},{\"name\":\"Saint Vincent and the Grenadines\",\"mask\":\"+1 (784)999-9999\",\"iso2\":\"vc\",\"dial\":\"+1 (784)\"},{\"name\":\"Samoa\",\"mask\":\"+685-99-9999\",\"iso2\":\"ws\",\"dial\":\"+685\"},{\"name\":\"San Marino\",\"mask\":\"+378-9999-999999\",\"iso2\":\"sm\",\"dial\":\"+378\"},{\"name\":\"Sao Tome and Principe (São Tomé e Príncipe)\",\"mask\":\"+239-99-99999\",\"iso2\":\"st\",\"dial\":\"+239\"},{\"name\":\"Saudi Arabia (المملكة العربية السعودية‎)\",\"mask\":\"+966-9-9999-9999\",\"iso2\":\"sa\",\"dial\":\"+966\"},{\"name\":\"Senegal (Sénégal)\",\"mask\":\"+221-99-999-9999\",\"iso2\":\"sn\",\"dial\":\"+221\"},{\"name\":\"Serbia (Србија)\",\"mask\":\"+381-99-999-9999\",\"iso2\":\"rs\",\"dial\":\"+381\"},{\"name\":\"Seychelles\",\"mask\":\"+248-9-999-999\",\"iso2\":\"sc\",\"dial\":\"+248\"},{\"name\":\"Sierra Leone\",\"mask\":\"+232-99-999999\",\"iso2\":\"sl\",\"dial\":\"+232\"},{\"name\":\"Singapore\",\"mask\":\"+65-9999-9999\",\"iso2\":\"sg\",\"dial\":\"+65\"},{\"name\":\"Slovakia (Slovensko)\",\"mask\":\"+421(999) 999-999\",\"iso2\":\"sk\",\"dial\":\"+421\"},{\"name\":\"Slovenia (Slovenija)\",\"mask\":\"+386-99-999-999\",\"iso2\":\"si\",\"dial\":\"+386\"},{\"name\":\"Solomon Islands\",\"mask\":\"+677-999-9999\",\"iso2\":\"sb\",\"dial\":\"+677\"},{\"name\":\"Somalia (Soomaaliya)\",\"mask\":\"+252-99-999-999\",\"iso2\":\"so\",\"dial\":\"+252\"},{\"name\":\"South Africa\",\"mask\":\"+27-99-999-9999\",\"iso2\":\"za\",\"dial\":\"+27\"},{\"name\":\"South Korea (대한민국)\",\"mask\":\"+82-99-9999-9999\",\"iso2\":\"kr\",\"dial\":\"+82\"},{\"name\":\"South Sudan (جنوب السودان‎)\",\"mask\":\"+211-99-999-9999\",\"iso2\":\"ss\",\"dial\":\"+211\"},{\"name\":\"Spain (España)\",\"mask\":\"+34(999) 999-999\",\"iso2\":\"es\",\"dial\":\"+34\"},{\"name\":\"Sri Lanka (ශ්‍රී ලංකාව)\",\"mask\":\"+94-99-999-9999\",\"iso2\":\"lk\",\"dial\":\"+94\"},{\"name\":\"Sudan (السودان‎)\",\"mask\":\"+249-99-999-9999\",\"iso2\":\"sd\",\"dial\":\"+249\"},{\"name\":\"Suriname\",\"mask\":\"+597-999-9999\",\"iso2\":\"sr\",\"dial\":\"+597\"},{\"name\":\"Swaziland\",\"mask\":\"+268-99-99-9999\",\"iso2\":\"sz\",\"dial\":\"+268\"},{\"name\":\"Sweden (Sverige)\",\"mask\":\"+46-99-999-9999\",\"iso2\":\"se\",\"dial\":\"+46\"},{\"name\":\"Switzerland (Schweiz)\",\"mask\":\"+41-99-999-9999\",\"iso2\":\"ch\",\"dial\":\"+41\"},{\"name\":\"Syria (سوريا‎)\",\"mask\":\"+963-99-9999-999\",\"iso2\":\"sy\",\"dial\":\"+963\"},{\"name\":\"Taiwan (台灣)\",\"mask\":\"+886-9999-9999\",\"iso2\":\"tw\",\"dial\":\"+886\"},{\"name\":\"Tajikistan\",\"mask\":\"+992-99-999-9999\",\"iso2\":\"tj\",\"dial\":\"+992\"},{\"name\":\"Tanzania\",\"mask\":\"+255-99-999-9999\",\"iso2\":\"tz\",\"dial\":\"+255\"},{\"name\":\"Thailand (ไทย)\",\"mask\":\"+66-99-999-9999\",\"iso2\":\"th\",\"dial\":\"+66\"},{\"name\":\"Togo\",\"mask\":\"+228-99-999-999\",\"iso2\":\"tg\",\"dial\":\"+228\"},{\"name\":\"Tonga\",\"mask\":\"+676-99999\",\"iso2\":\"to\",\"dial\":\"+676\"},{\"name\":\"Trinidad and Tobago\",\"mask\":\"+1 (868)999-9999\",\"iso2\":\"tt\",\"dial\":\"+1 (868)\"},{\"name\":\"Tunisia (تونس‎)\",\"mask\":\"+216-99-999-999\",\"iso2\":\"tn\",\"dial\":\"+216\"},{\"name\":\"Turkey (Türkiye)\",\"mask\":\"+90(999) 999-99999\",\"iso2\":\"tr\",\"dial\":\"+90\"},{\"name\":\"Turkmenistan\",\"mask\":\"+993-9-999-9999\",\"iso2\":\"tm\",\"dial\":\"+993\"},{\"name\":\"Tuvalu\",\"mask\":\"+688-999999\",\"iso2\":\"tv\",\"dial\":\"+688\"},{\"name\":\"Uganda\",\"mask\":\"+256(999) 999-999\",\"iso2\":\"ug\",\"dial\":\"+256\"},{\"name\":\"Ukraine (Україна)\",\"mask\":\"+380(99) 999-99-99\",\"iso2\":\"ua\",\"dial\":\"+380\"},{\"name\":\"United Arab Emirates (الإمارات العربية المتحدة‎)\",\"mask\":\"+971-99-999-9999\",\"iso2\":\"ae\",\"dial\":\"+971\"},{\"name\":\"United Kingdom\",\"mask\":\"+44-99-9999-99999\",\"iso2\":\"gb\",\"dial\":\"+44\"},{\"name\":\"USA\",\"mask\":\"+1(999) 999-9999\",\"iso2\":\"us\",\"dial\":\"+1\"},{\"name\":\"Uruguay\",\"mask\":\"+598-9-999-99-99\",\"iso2\":\"uy\",\"dial\":\"+598\"},{\"name\":\"Uzbekistan (Oʻzbekiston)\",\"mask\":\"+998-99-999-9999\",\"iso2\":\"uz\",\"dial\":\"+998\"},{\"name\":\"Vanuatu\",\"mask\":\"+678-99-99999\",\"iso2\":\"vu\",\"dial\":\"+678\"},{\"name\":\"Vatican City (Città del Vaticano)\",\"mask\":\"+39-9-999-99999\",\"iso2\":\"va\",\"dial\":\"+39\"},{\"name\":\"Venezuela\",\"mask\":\"+58(999) 999-9999\",\"iso2\":\"ve\",\"dial\":\"+58\"},{\"name\":\"Vietnam (Việt Nam)\",\"mask\":\"+84-99-9999-999\",\"iso2\":\"vn\",\"dial\":\"+84\"},{\"name\":\"Yemen (اليمن‎)\",\"mask\":\"+967-9-999-999\",\"iso2\":\"ye\",\"dial\":\"+967\"},{\"name\":\"Zambia\",\"mask\":\"+260-99-999-9999\",\"iso2\":\"zm\",\"dial\":\"+260\"},{\"name\":\"Zimbabwe\",\"mask\":\"+263-9-999999\",\"iso2\":\"zw\",\"dial\":\"+263\"}]";
  let COUNTRIES = null;

  function countryList(){
    if(!COUNTRIES) COUNTRIES = JSON.parse(COUNTRIES_JSON);
    return COUNTRIES;
  }

  const langRaw = (document.documentElement.lang || 'ru').toLowerCase();
  const lang = langRaw.startsWith('en') ? 'en' : (langRaw.startsWith('zh') || langRaw === 'cn' ? 'cn' : 'ru');

  const copy = {
    ru: {
      eyebrow:'IndexResearch',
      modalTitle:'Обсудить исследование',
      modalLead:'Оставьте контакты и коротко опишите задачу: рейтинг, сравнительное исследование, данные или редакционный вопрос.',
      inlineEyebrow:'Связаться',
      inlineTitle:'Заказать или обсудить исследование',
      inlineLead:'Опишите задачу. Для ответа достаточно телефона или email.',
      name:'ФИО',
      phone:'Телефон',
      email:'Email',
      comment:'Что нужно исследовать или обсудить',
      submit:'Отправить запрос',
      consentPrefix:'Нажимая кнопку, пользователь соглашается с ',
      privacy:'политикой конфиденциальности',
      consentJoin:' и ',
      personal:'обработкой персональных данных',
      close:'Закрыть форму',
      requiredName:'Укажите ФИО.',
      requiredContact:'Укажите телефон или email.',
      invalidPhone:'Проверьте номер телефона.',
      invalidEmail:'Проверьте email.',
      unavailable:'Отправка пока не подключена. Можно написать на research@indexresearch.ru.',
      sending:'Отправляем...',
      success:'Спасибо. Сообщение отправлено.',
      serverError:'Не удалось отправить сообщение. Попробуйте еще раз или напишите на research@indexresearch.ru.',
      country:'Выбрать страну'
    },
    en: {
      eyebrow:'IndexResearch',
      modalTitle:'Discuss a research project',
      modalLead:'Leave your contact details and briefly describe the task: a ranking, comparative study, data request, or editorial question.',
      inlineEyebrow:'Contact',
      inlineTitle:'Commission or discuss a research project',
      inlineLead:'Describe the task. A phone number or email is enough for us to reply.',
      name:'Full name',
      phone:'Phone',
      email:'Email',
      comment:'What would you like to research or discuss?',
      submit:'Send request',
      consentPrefix:'By clicking the button, you agree to the ',
      privacy:'Privacy Policy',
      consentJoin:' and ',
      personal:'Personal Data Processing terms',
      close:'Close form',
      requiredName:'Enter your full name.',
      requiredContact:'Enter a phone number or email.',
      invalidPhone:'Check the phone number.',
      invalidEmail:'Check the email address.',
      unavailable:'Submission is not connected yet. You can email research@indexresearch.ru.',
      sending:'Sending...',
      success:'Thank you. Your message has been sent.',
      serverError:'Could not send the message. Please try again or email research@indexresearch.ru.',
      country:'Choose country'
    },
    cn: {
      eyebrow:'IndexResearch',
      modalTitle:'讨论研究项目',
      modalLead:'请留下联系方式，并简要说明需求：排名、比较研究、数据请求或编辑相关问题。',
      inlineEyebrow:'联系',
      inlineTitle:'委托或讨论研究项目',
      inlineLead:'请说明需求。留下电话或电子邮箱其中一项即可。',
      name:'姓名',
      phone:'电话',
      email:'电子邮箱',
      comment:'您希望研究或讨论什么？',
      submit:'提交请求',
      consentPrefix:'点击按钮即表示您同意',
      privacy:'隐私政策',
      consentJoin:'以及',
      personal:'个人数据处理条款',
      close:'关闭表单',
      requiredName:'请输入姓名。',
      requiredContact:'请输入电话号码或电子邮箱。',
      invalidPhone:'请检查电话号码。',
      invalidEmail:'请检查电子邮箱地址。',
      unavailable:'发送功能尚未接通。您也可以写信至 research@indexresearch.ru。',
      sending:'正在发送...',
      success:'谢谢，您的消息已发送。',
      serverError:'发送失败。请稍后重试，或写信至 research@indexresearch.ru。',
      country:'选择国家'
    }
  }[lang];

  const defaultIso = lang === 'en' ? 'us' : (lang === 'cn' ? 'cn' : 'ru');
  const privacyHref = lang === 'en' ? '/en/privacy-policy/' : (lang === 'cn' ? '/cn/privacy-policy/' : '/privacy-policy/');
  const personalHref = lang === 'en' ? '/en/personal-data-consent/' : (lang === 'cn' ? '/cn/personal-data-consent/' : '/personal-data-consent/');

  function injectStyles(){}

  function maskParts(country){
    const full = country.mask || '';
    const rest = full.indexOf(country.dial) === 0 ? full.slice(country.dial.length) : full;
    return {pattern:rest, digits:(rest.match(/9/g) || []).length};
  }

  function formatNational(value, country){
    const meta = maskParts(country);
    let digits = String(value || '').replace(/\D/g,'');
    const dialDigits = String(country.dial || '').replace(/\D/g,'');
    if(digits.indexOf(dialDigits) === 0 && digits.length > meta.digits) digits = digits.slice(dialDigits.length);
    digits = digits.slice(0, meta.digits);
    let out = '';
    let di = 0;
    for(let i=0;i<meta.pattern.length;i++){
      const ch = meta.pattern[i];
      if(ch === '9'){
        if(di >= digits.length) break;
        out += digits[di++];
      }else if(di > 0 || digits.length > 0){
        out += ch;
      }
    }
    return out;
  }

  function phonePlaceholder(country){
    return maskParts(country).pattern.replace(/9/g,'0').trim();
  }

  function normalizePhone(country, national){
    const dialDigits = String(country.dial || '').replace(/\D/g,'');
    let localDigits = String(national || '').replace(/\D/g,'');
    const expected = maskParts(country).digits;
    if(localDigits.indexOf(dialDigits) === 0 && localDigits.length > expected) localDigits = localDigits.slice(dialDigits.length);
    return localDigits ? '+' + dialDigits + localDigits : '';
  }

  function getCountry(iso){
    return countryList().find(function(c){ return c.iso2 === iso; }) || countryList().find(function(c){ return c.iso2 === defaultIso; }) || countryList()[0];
  }

  function flagUrl(iso){
    return 'https://flagcdn.com/' + iso + '.svg';
  }

  function flagPngUrl(iso, width){
    return 'https://flagcdn.com/' + width + 'x' + Math.round(width * .75) + '/' + iso + '.png';
  }

  function setFlagSource(img, iso, width){
    img.onerror = function(){
      img.onerror = null;
      img.src = flagPngUrl(iso,width);
    };
    img.src = flagUrl(iso);
  }

  function createPhoneField(formId){
    let selected = getCountry(defaultIso);
    const field = document.createElement('div');
    field.className = 'ir-form-field';
    field.innerHTML =
      '<div class="ir-phone-wrap">' +
        '<button type="button" class="ir-country-toggle" aria-haspopup="listbox" aria-expanded="false" aria-label="' + copy.country + '">' +
          '<img class="ir-country-flag" alt="" width="24" height="18">' +
          '<span class="ir-country-code"></span><span class="ir-country-chevron" aria-hidden="true"></span>' +
        '</button>' +
        '<input class="ir-form-input ir-phone-input" type="tel" inputmode="tel" autocomplete="tel-national" name="phone_national" aria-label="' + copy.phone + '">' +
        '<div class="ir-country-menu" role="listbox" data-nosnippet></div>' +
      '</div>';

    const wrap = field.querySelector('.ir-phone-wrap');
    const toggle = field.querySelector('.ir-country-toggle');
    const flag = field.querySelector('.ir-country-flag');
    const code = field.querySelector('.ir-country-code');
    const input = field.querySelector('.ir-phone-input');
    const menu = field.querySelector('.ir-country-menu');
    let menuBuilt = false;

    function applyCountry(country, focusInput){
      selected = country;
      setFlagSource(flag,country.iso2,24);
      code.textContent = country.dial;
      input.placeholder = phonePlaceholder(country);
      input.value = formatNational(input.value,country);
      input.dataset.iso2 = country.iso2;
      input.dataset.dial = country.dial;
      input.dataset.mask = country.mask;
      toggle.setAttribute('aria-label', copy.country + ': ' + country.name + ' ' + country.dial);
      menu.classList.remove('is-open');
      toggle.setAttribute('aria-expanded','false');
      wrap.classList.remove('is-invalid');
      if(focusInput) input.focus();
    }

    function buildMenu(){
      if(menuBuilt) return;
      menuBuilt = true;
      const frag = document.createDocumentFragment();
      countryList().forEach(function(country){
        const option = document.createElement('button');
        option.type = 'button';
        option.className = 'ir-country-option';
        option.setAttribute('role','option');
        option.dataset.iso2 = country.iso2;
        option.innerHTML =
          '<img class="ir-country-flag" alt="" width="24" height="18">' +
          '<span>' + country.name + '</span>' +
          '<span class="ir-country-option-code">' + country.dial + '</span>';
        setFlagSource(option.querySelector('.ir-country-flag'),country.iso2,24);
        option.addEventListener('click',function(){ applyCountry(country,true); });
        frag.appendChild(option);
      });
      menu.appendChild(frag);
    }

    toggle.addEventListener('click',function(){
      buildMenu();
      const open = !menu.classList.contains('is-open');
      menu.classList.toggle('is-open',open);
      toggle.setAttribute('aria-expanded',open ? 'true' : 'false');
      if(open){
        const selectedOption = menu.querySelector('[data-iso2="' + selected.iso2 + '"]');
        if(selectedOption) setTimeout(function(){
          const targetTop = selectedOption.offsetTop - Math.max(0,(menu.clientHeight - selectedOption.offsetHeight) / 2);
          menu.scrollTop = Math.max(0,targetTop);
        },0);
      }
    });

    input.addEventListener('input',function(){
      const formatted = formatNational(input.value,selected);
      if(input.value !== formatted) input.value = formatted;
      wrap.classList.remove('is-invalid');
    });

    document.addEventListener('click',function(e){
      if(!field.contains(e.target)){
        menu.classList.remove('is-open');
        toggle.setAttribute('aria-expanded','false');
      }
    });

    applyCountry(selected,false);

    return {
      field:field,
      getCountry:function(){ return selected; },
      input:input,
      wrap:wrap,
      isValid:function(){
        if(!input.value.trim()) return true;
        return (input.value.match(/\d/g) || []).length === maskParts(selected).digits;
      },
      normalized:function(){ return normalizePhone(selected,input.value); }
    };
  }

  function createConsent(){
    const consent = document.createElement('div');
    consent.className = 'ir-form-consent';
    const p1 = document.createTextNode(copy.consentPrefix);
    const privacy = document.createElement('a');
    privacy.href = privacyHref;
    privacy.textContent = copy.privacy;
    const join = document.createTextNode(copy.consentJoin);
    const personal = document.createElement('a');
    personal.href = personalHref;
    personal.textContent = copy.personal;
    consent.append(p1,privacy,join,personal,document.createTextNode('.'));
    return consent;
  }

  function readTracking(){
    const qs = new URLSearchParams(location.search);
    const utm = {};
    ['utm_source','utm_medium','utm_campaign','utm_content','utm_term','utm_id','gclid','yclid','ysclid'].forEach(function(k){
      if(qs.get(k)) utm[k] = qs.get(k);
    });
    try{
      if(window.IndexResearchAnalytics && typeof window.IndexResearchAnalytics.getTracking === 'function'){
        return Object.assign({},window.IndexResearchAnalytics.getTracking(),utm);
      }
      const stored = JSON.parse(sessionStorage.getItem('indexresearch_tracking_v1') || '{}');
      return Object.assign({},stored,utm);
    }catch(e){
      return utm;
    }
  }

  function buildForm(mode){
    const shell = document.createElement('div');
    shell.className = 'ir-form-shell ir-form-' + mode;
    const form = document.createElement('form');
    form.className = 'ir-lead-form';
    form.noValidate = true;
    const formId = 'ir-lead-' + mode + '-' + Math.random().toString(36).slice(2,8);

    const nameField = document.createElement('div');
    nameField.className = 'ir-form-field';
    nameField.innerHTML = '<label class="ir-hp" for="' + formId + '-name">' + copy.name + '</label><input id="' + formId + '-name" class="ir-form-input" name="full_name" type="text" autocomplete="name" placeholder="' + copy.name + '" maxlength="180">';

    const phone = createPhoneField(formId);

    const emailField = document.createElement('div');
    emailField.className = 'ir-form-field ir-form-field--wide';
    emailField.innerHTML = '<label class="ir-hp" for="' + formId + '-email">' + copy.email + '</label><input id="' + formId + '-email" class="ir-form-input" name="email" type="email" inputmode="email" autocomplete="email" placeholder="' + copy.email + '" maxlength="254">';

    const commentField = document.createElement('div');
    commentField.className = 'ir-form-field ir-form-field--wide';
    commentField.innerHTML = '<label class="ir-hp" for="' + formId + '-comment">' + copy.comment + '</label><textarea id="' + formId + '-comment" class="ir-form-textarea" name="comment" placeholder="' + copy.comment + '" maxlength="3000"></textarea>';

    const hp = document.createElement('div');
    hp.className = 'ir-hp';
    hp.setAttribute('aria-hidden','true');
    hp.innerHTML = '<label>Website<input type="text" name="company_website" tabindex="-1" autocomplete="off"></label>';

    const actions = document.createElement('div');
    actions.className = 'ir-form-actions';
    const submit = document.createElement('button');
    submit.className = 'ir-form-submit';
    submit.type = 'submit';
    submit.textContent = copy.submit;
    actions.appendChild(submit);

    const status = document.createElement('p');
    status.className = 'ir-form-status';
    status.setAttribute('role','status');
    status.setAttribute('aria-live','polite');

    form.append(nameField,phone.field,emailField,commentField,hp,actions,status,createConsent());
    shell.appendChild(form);

    const nameInput = form.elements.full_name;
    const emailInput = form.elements.email;
    const commentInput = form.elements.comment;
    const hpInput = form.elements.company_website;
    const createdAt = Date.now();

    function setStatus(message,type){
      status.textContent = message || '';
      status.classList.toggle('is-error',type === 'error');
      status.classList.toggle('is-success',type === 'success');
    }

    function validate(){
      nameInput.setAttribute('aria-invalid','false');
      emailInput.setAttribute('aria-invalid','false');
      phone.wrap.classList.remove('is-invalid');
      setStatus('',null);

      if(!nameInput.value.trim()){
        nameInput.setAttribute('aria-invalid','true');
        nameInput.focus();
        setStatus(copy.requiredName,'error');
        return false;
      }

      const hasPhone = !!phone.input.value.trim();
      const hasEmail = !!emailInput.value.trim();
      if(!hasPhone && !hasEmail){
        phone.wrap.classList.add('is-invalid');
        emailInput.setAttribute('aria-invalid','true');
        phone.input.focus();
        setStatus(copy.requiredContact,'error');
        return false;
      }

      if(hasPhone && !phone.isValid()){
        phone.wrap.classList.add('is-invalid');
        phone.input.focus();
        setStatus(copy.invalidPhone,'error');
        return false;
      }

      if(hasEmail && !emailInput.validity.valid){
        emailInput.setAttribute('aria-invalid','true');
        emailInput.focus();
        setStatus(copy.invalidEmail,'error');
        return false;
      }

      return true;
    }

    nameInput.addEventListener('input',function(){ nameInput.setAttribute('aria-invalid','false'); });
    emailInput.addEventListener('input',function(){ emailInput.setAttribute('aria-invalid','false'); });

    form.addEventListener('submit',async function(e){
      e.preventDefault();
      if(!validate()) return;

      if(hpInput.value){
        setStatus(copy.success,'success');
        form.reset();
        return;
      }

      if(!FORM_ENDPOINT){
        setStatus(copy.unavailable,'error');
        return;
      }

      const payload = {
        site:'indexresearch',
        lang:lang,
        full_name:nameInput.value.trim(),
        phone:phone.normalized(),
        phone_country:phone.getCountry().iso2,
        email:emailInput.value.trim(),
        comment:commentInput.value.trim(),
        company_website:hpInput.value,
        page_url:location.href,
        referrer:document.referrer || '',
        utm:readTracking(),
        form_started_at:new Date(createdAt).toISOString(),
        submitted_at:new Date().toISOString()
      };

      submit.disabled = true;
      setStatus(copy.sending,null);
      try{
        const response = await fetch(FORM_ENDPOINT,{
          method:'POST',
          headers:{'Content-Type':'application/json'},
          credentials:'omit',
          body:JSON.stringify(payload)
        });
        if(!response.ok) throw new Error('HTTP ' + response.status);
        setStatus(copy.success,'success');
        document.dispatchEvent(new CustomEvent('indexresearch:lead-success',{detail:{mode:mode,lang:lang}}));
        form.reset();
        phone.input.value = '';
      }catch(err){
        setStatus(copy.serverError,'error');
      }finally{
        submit.disabled = false;
      }
    });

    shell._irNameInput = nameInput;
    return shell;
  }

  function isHomePage(){
    return ['/', '/index.html', '/en/', '/en/index.html', '/cn/', '/cn/index.html'].indexOf(location.pathname) !== -1;
  }

  function ensureInlineShell(){
    if(!isHomePage()) return null;
    let section = document.getElementById('contact');
    if(section) return section;

    section = document.createElement('section');
    section.id = 'contact';
    section.className = 'section alt ir-contact-section';
    section.innerHTML =
      '<div class="wrap ir-contact-layout">' +
        '<div class="ir-contact-copy">' +
          '<p class="kicker">' + copy.inlineEyebrow + '</p>' +
          '<h2>' + copy.inlineTitle + '</h2>' +
          '<p class="ir-contact-lead">' + copy.inlineLead + '</p>' +
          '<p class="ir-contact-email"><a href="mailto:research@indexresearch.ru">research@indexresearch.ru</a></p>' +
        '</div>' +
        '<div class="ir-contact-form" data-indexresearch-form-mount></div>' +
      '</div>';

    const footer = document.querySelector('footer');
    if(footer && footer.parentNode) footer.parentNode.insertBefore(section, footer);
    else document.body.appendChild(section);

    if(location.hash === '#contact'){
      requestAnimationFrame(function(){ section.scrollIntoView({block:'start'}); });
    }
    return section;
  }

  function upgradeInlineForm(){
    const lead = ensureInlineShell();
    if(!lead) return;
    const mount = lead.querySelector('[data-indexresearch-form-mount]');
    if(!mount || mount.dataset.indexresearchUpgraded === 'true') return;
    mount.dataset.indexresearchUpgraded = 'true';
    mount.appendChild(buildForm('inline'));
  }

  let overlay = null;
  let lastOpener = null;

  function closeModal(){
    if(!overlay) return;
    const old = overlay;
    overlay = null;
    old.remove();
    document.body.classList.remove('ir-modal-open');
    document.removeEventListener('keydown',onModalKeydown);
    if(lastOpener && typeof lastOpener.focus === 'function') lastOpener.focus();
    lastOpener = null;
  }

  function onModalKeydown(e){
    if(!overlay) return;
    if(e.key === 'Escape'){
      e.preventDefault();
      closeModal();
      return;
    }
    if(e.key !== 'Tab') return;
    const focusable = Array.from(overlay.querySelectorAll('button,input,textarea,a[href]')).filter(function(el){ return !el.disabled && el.offsetParent !== null; });
    if(!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length-1];
    if(e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
    else if(!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
  }

  function openModal(opener){
    if(overlay) return;
    lastOpener = opener || document.activeElement;

    overlay = document.createElement('div');
    overlay.className = 'ir-modal-overlay';
    overlay.innerHTML =
      '<div class="ir-modal" role="dialog" aria-modal="true" aria-labelledby="ir-modal-title">' +
        '<button type="button" class="ir-modal-close" aria-label="' + copy.close + '"></button>' +
        '<div class="ir-modal-head">' +
          '<div class="ir-modal-eyebrow">' + copy.eyebrow + '</div>' +
          '<h2 class="ir-modal-title" id="ir-modal-title">' + copy.modalTitle + '</h2>' +
          '<p class="ir-modal-lead">' + copy.modalLead + '</p>' +
        '</div>' +
      '</div>';

    const dialog = overlay.querySelector('.ir-modal');
    const formShell = buildForm('modal');
    dialog.appendChild(formShell);
    document.body.appendChild(overlay);
    document.body.classList.add('ir-modal-open');

    overlay.querySelector('.ir-modal-close').addEventListener('click',closeModal);
    overlay.addEventListener('mousedown',function(e){ if(e.target === overlay) closeModal(); });
    document.addEventListener('keydown',onModalKeydown);
    setTimeout(function(){ if(formShell._irNameInput) formShell._irNameInput.focus(); },0);
  }

  function isLeadTrigger(anchor){
    const href = anchor.getAttribute('href') || '';
    if(!href || href.charAt(0) === 'j') return false;
    try{
      const url = new URL(href,location.href);
      return url.hash === '#contact' && (url.origin === location.origin || url.hostname === 'indexresearch.ru' || url.hostname === 'www.indexresearch.ru' || url.hostname === 'indexresearch-ru.github.io');
    }catch(e){
      return false;
    }
  }

  document.addEventListener('click',function(e){
    const anchor = e.target.closest && e.target.closest('a[href]');
    if(!anchor || !isLeadTrigger(anchor)) return;
    if(e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    document.querySelectorAll('.menu-mobile[open]').forEach(function(menu){ menu.removeAttribute('open'); });
    ensureLeadUiReady();
    openModal(anchor);
  });

  let leadUiReady = false;

  function ensureLeadUiReady(){
    if(leadUiReady) return;
    leadUiReady = true;
    injectStyles();
    upgradeInlineForm();
  }

  const leadSection = ensureInlineShell();
  if(leadSection){
    // The inline form is lightweight: the country menu is still built lazily on first use.
    // Mount immediately so the contact block is never rendered half-empty because of
    // IntersectionObserver timing, browser throttling or cached page state.
    ensureLeadUiReady();
  }

  document.addEventListener('pointerdown',function(e){
    const anchor = e.target.closest && e.target.closest('a[href]');
    if(anchor && isLeadTrigger(anchor)) ensureLeadUiReady();
  }, {passive:true,capture:true});

  document.addEventListener('focusin',function(e){
    const anchor = e.target.closest && e.target.closest('a[href]');
    if(anchor && isLeadTrigger(anchor)) ensureLeadUiReady();
  }, {passive:true});

  window.IndexResearchLeadForm = {
    open:function(opener){ ensureLeadUiReady(); openModal(opener); },
    close:closeModal
  };
})();
