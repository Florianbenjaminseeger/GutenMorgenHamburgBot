# Telegram AI Chatbot

Ein persönlicher Telegram-Bot mit Google Gemini AI Integration, Wetterbericht für Hamburg und iCloud-Kalenderanbindung.

## Funktionen

*   **AI Chat**: Unterhalte dich ganz normal mit dem Bot (powered by Google Gemini).
*   **Daily Briefing**: Jeden Morgen um 07:00 Uhr gibt es das Wetter und deine Termine für den Tag.
*   **Love Message**: Jeden Morgen um 07:00 Uhr bekommt deine Freundin automatisch eine süße, AI-generierte Nachricht.
*   **Befehle**:
    *   `/start` - Begrüßung und Initialisierung.
    *   `/weather` - Aktuelles Wetter in Hamburg.
    *   `/briefing` - Wetter + Kalender sofort abrufen.
    *   `/love` - Sofort eine Liebesnachricht an den aktuellen Chat senden.
    *   `/id` - Zeigt die eigene Chat-ID an.

## Installation & Start

1.  Sicherstellen, dass die `.env` Datei mit den Zugangsdaten gefüllt ist.
2.  Starten mit:
    ```bash
    run.bat
    ```

## Voraussetzungen

*   Python 3.12+
*   Packages in `requirements.txt`
*   Telegram Bot Token
*   Google Gemini API Key
*   iCloud App-Specific Password (für Kalender)
