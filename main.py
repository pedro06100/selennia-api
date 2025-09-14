import os
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from quart import Quart, request, jsonify
from dotenv import load_dotenv

load_dotenv()
app = Quart(__name__)

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASS = os.getenv("GMAIL_PASS")

def envoyer_mail_sync(subject: str, body: str, files=None):
    """Envoi d'email via Gmail avec pièces jointes"""
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = GMAIL_USER  # tu peux changer ici si tu veux envoyer ailleurs
        msg["Subject"] = subject

        # Corps du message
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Pièces jointes
        if files:
            for file in files:
                try:
                    file.seek(0)
                    file_data = file.read()
                    if not file_data:
                        continue

                    # Détection du type MIME
                    ctype, encoding = mimetypes.guess_type(file.filename)
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"

                    maintype, subtype = ctype.split("/", 1)

                    if maintype == "image":
                        part = MIMEImage(file_data, _subtype=subtype)
                    else:
                        part = MIMEApplication(file_data, _subtype=subtype)

                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=file.filename
                    )
                    msg.attach(part)

                except Exception as file_error:
                    print(f"Erreur avec le fichier {getattr(file, 'filename', '?')}: {file_error}")
                    continue

        # Envoi
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, [GMAIL_USER], msg.as_string())

        print(f"✅ Email envoyé avec succès: {subject}")

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi de l'email: {e}")
        raise e

# ------------------------
# ROUTES QUART
# ------------------------

@app.route("/test-email", methods=["POST"])
async def test_email():
    """Route pour tester l'envoi d'email"""
    try:
        envoyer_mail_sync("Test Selennia API", "Ceci est un test d'envoi d'email depuis l'API Selennia.")
        return jsonify({"success": "Email de test envoyé avec succès"}), 200
    except Exception as e:
        return jsonify({"error": f"Erreur lors du test: {str(e)}"}), 500


@app.route("/contact", methods=["POST"])
async def contact():
    try:
        data = await request.form
        nom = data.get("name")
        email = data.get("email")
        sujet = data.get("subject", "Message depuis le site")
        message = data.get("message")

        if not nom or not email or not message:
            return jsonify({"error": "Champs manquants"}), 400

        body = f"""
📩 Nouveau message de contact Selennia Boutique

Nom : {nom}
Email : {email}
Sujet : {sujet}

Message :
{message}

---
Envoyé depuis le formulaire de contact du site Selennia Boutique
"""

        envoyer_mail_sync(f"Contact Selennia - {sujet}", body)
        return jsonify({"success": "Message envoyé avec succès"}), 200

    except Exception as e:
        print(f"Erreur dans /contact: {e}")
        return jsonify({"error": "Erreur lors de l'envoi du message"}), 500


@app.route("/estimation", methods=["POST"])
async def estimation():
    try:
        data = await request.form
        files = await request.files

        nom = data.get("name")
        email = data.get("email")
        tel = data.get("phone", "Non renseigné")
        objet = data.get("object-type")
        description = data.get("description")

        if not nom or not email or not objet or not description:
            return jsonify({"error": "Champs manquants"}), 400

        body = f"""
📷 Nouvelle demande d'estimation Selennia Boutique

Nom : {nom}
Email : {email}
Téléphone : {tel}
Type d'objet : {objet}

Description :
{description}

---
Nombre de photos jointes : {len(files) if files else 0}
Envoyé depuis le formulaire d'estimation du site Selennia Boutique
"""

        # Récupérer les fichiers photos
        photo_files = []
        if files:
            for _, file in files.items():
                if file and file.filename:
                    photo_files.append(file)

        envoyer_mail_sync("Demande d'estimation Selennia", body, files=photo_files if photo_files else None)
        return jsonify({"success": "Demande envoyée avec succès"}), 200

    except Exception as e:
        print(f"Erreur dans /estimation: {e}")
        return jsonify({"error": "Erreur lors de l'envoi de la demande"}), 500


@app.route("/test", methods=["GET"])
async def test():
    return jsonify({
        "status": "API Selennia Boutique fonctionnelle",
        "gmail_user": GMAIL_USER,
        "gmail_configured": bool(GMAIL_USER and GMAIL_PASS)
    }), 200


@app.after_request
async def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response


if __name__ == "__main__":
    if not GMAIL_USER or not GMAIL_PASS:
        print("❌ Erreur: GMAIL_USER et GMAIL_PASS doivent être définis dans le fichier .env")
        print("📋 Instructions:")
        print("   1. Activez l'authentification à 2 facteurs sur Gmail")
        print("   2. Générez un mot de passe d'application")
        print("   3. Ajoutez GMAIL_USER et GMAIL_PASS dans votre fichier .env")
        exit(1)

    print(f"🚀 API Selennia démarrée avec l'email: {GMAIL_USER}")
    print(f"🧪 Testez l'envoi d'email: POST /test-email")
    app.run(debug=True)
