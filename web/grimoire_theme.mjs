// Local CSS only: no fonts, textures or trackers are fetched from external services.
export const grimoireTheme=`
.grimoire-app{
    --line:#675039;--muted:#c5b6a0;position:relative;isolation:isolate;
    color:#f0e5d1;border:1px solid #ad8449;border-radius:12px;
    background:radial-gradient(ellipse at 10% 0%,#512c6940,transparent 55%),radial-gradient(ellipse at 100% 100%,#9861241b,transparent 50%),#15101d;
    box-shadow:inset 0 0 0 3px #1c1423,inset 0 0 0 4px #b28a3e33,0 8px 25px #0005;
}
.grimoire-app::before{content:'';position:absolute;inset:5px;border:1px solid #c89a4b25;border-radius:8px;pointer-events:none;z-index:0}
.grimoire-app::after{content:'';position:absolute;right:-95px;bottom:120px;width:290px;height:290px;border:1px solid #bc96ef10;border-radius:50%;box-shadow:0 0 0 18px #bc96ef06,0 0 0 20px #bc96ef0a,0 0 0 52px #bc96ef04;pointer-events:none;z-index:0}
.grimoire-app>*{position:relative;z-index:1}
.grimoire-app .gm-header{background:linear-gradient(100deg,#302035e8,#241929e8);border-bottom-color:#b38b4a70}
.grimoire-app .gm-header strong{font-family:Georgia,serif;color:#efca7a;font-size:24px;text-shadow:0 0 14px #c69bfba0}
.grimoire-app :is(button,select,input,textarea){background:#211925;border-color:#6f5542;color:#efe3cc;box-shadow:inset 0 1px #f8dea00a}
.grimoire-app button{font-family:'Palatino Linotype','Book Antiqua',Georgia,serif;background:linear-gradient(#3b293e,#291d2e);letter-spacing:.015em;transition:background .18s,box-shadow .18s,border-color .18s}
.grimoire-app button:hover{background:linear-gradient(#50364f,#352438);border-color:#c39a5f;box-shadow:0 0 10px #b383ea30}
.grimoire-app :is(button,select,input,textarea):focus-visible{outline-color:#e2bd77}
.grimoire-app .gm-tabs{background:#1a1421c9;border-bottom-color:#7e60443d}
.grimoire-app .gm-tabs button{background:transparent;color:#c7b7aa;font-family:Georgia,serif}
.grimoire-app .gm-tabs button[aria-selected=true]{color:#f6d58b;box-shadow:inset 0 -2px #dcb56e;text-shadow:0 0 10px #dab66b55}
.grimoire-app .gm-toolbar{background:linear-gradient(90deg,#24182ac4,#19121f9c);border-bottom-color:#9e774747}
.grimoire-app .gm-toolbar label{color:#dbbf8c}
.grimoire-app .gm-applied{background:#251a2a80;border-color:#936e424d}
.grimoire-app summary,.grimoire-app a{color:#e4c693}
.grimoire-app .gm-history{scrollbar-color:#816149 #17111d;scrollbar-width:thin}
.grimoire-app .gm-message{position:relative;border:1px solid #86694466;border-radius:6px 16px 16px 16px;box-shadow:0 5px 14px #0003,inset 0 1px #efcb7e0b}
.grimoire-app .gm-assistant{background:linear-gradient(135deg,#302237ed,#201925f2);border-bottom-left-radius:4px}
.grimoire-app .gm-user{background:linear-gradient(135deg,#694978,#493352);border-color:#c497ae66;border-radius:16px 6px 4px 16px}
.grimoire-app .gm-role{display:flex;align-items:center;flex-wrap:wrap;gap:8px;color:#d9b97e;font-family:Georgia,serif;letter-spacing:.025em}
.grimoire-app .gm-message-actions{border-top-color:#b88b4533}
.grimoire-app .gm-message-actions button{color:#ead4ad;border-color:#97754566}
.grimoire-app .gm-message :is(h1,h2,h3,h4){font-family:Georgia,serif;color:#f2d8a8}
.grimoire-app pre{background:#120e17!important;color:#f0e1c7;border:1px solid #a27b452e;border-radius:6px}
.grimoire-app code{color:#ead9bc}
.grimoire-app .gm-composer{background:#19121ec9;border-top-color:#aa80504d}
.grimoire-app .gm-composer textarea{background:#110d17;border-color:#8d6b45;box-shadow:inset 0 2px 8px #0005;color:#f0e5d1}
.grimoire-app .gm-footer{background:#19121ec9}
.grimoire-app .gm-primary{background:linear-gradient(135deg,#c9a35d,#8e6739);color:#1c1221;border-color:#edce8f;box-shadow:0 0 12px #cfab4930,inset 0 1px #fff4}
.grimoire-app .gm-primary:hover{background:linear-gradient(135deg,#e1be77,#b2874e);color:#1c1221}
.grimoire-app .gm-form{background:#18121ec9}
.grimoire-app .mage-api-key{background:#241a2c;border-color:#8f6d4255}
.grimoire-app .gm-empty{color:#c7b294;font-family:Georgia,serif}
.grimoire-app .gm-attachment{background:#302235;border-color:#886d4c}
.grimoire-app .gm-applied-badge{display:inline-block;padding:3px 8px;border:1px solid #e6bc69;border-radius:5px;background:#e4bc6a19;color:#ffdfa0;font:600 11px/1.4 system-ui,sans-serif;max-width:100%;overflow-wrap:anywhere}
.grimoire-app .gm-message.gm-selected{border-color:#e5bd70;background:linear-gradient(135deg,#3d2c46f5,#251a2df5);box-shadow:0 0 0 1px #b899e944,0 0 18px #bd91ef55,inset 0 0 24px #dab56a16;animation:gm-bound-glow 4s ease-in-out infinite}
.grimoire-app .gm-selected .gm-message-actions button[aria-pressed=true]{color:#ffdfa0;background:#d4aa4c20;border-color:#e1ba70;opacity:1}
@keyframes gm-bound-glow{0%,100%{box-shadow:0 0 0 1px #b899e944,0 0 14px #bd91ef44,inset 0 0 20px #dab56a12}50%{box-shadow:0 0 0 1px #d4af7970,0 0 22px #bd91ef77,inset 0 0 26px #dab56a20}}
@media(prefers-reduced-motion:reduce){.grimoire-app .gm-message.gm-selected{animation:none}.grimoire-app button{transition:none}}
`;
