import time

from playwright.sync_api import sync_playwright


def capture():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Ajusta viewport para um tamanho Desktop
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        print("Acessando aplicação...")
        try:
            page.goto("http://localhost:8501", timeout=10000)
            page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"Erro ao acessar localhost: {e}")
            return

        # Aguarda Streamlit carregar
        time.sleep(3)

        print("Navegando para Detetive IA...")
        # Tenta clicar no link da sidebar
        # O seletor pode variar, vamos tentar pelo texto
        try:
            # Expande sidebar se necessário (em mobile, mas estamos em desktop 1280px)
            # Localiza elemento com texto "Detetive IA"
            page.get_by_text("Detetive IA").click()
            time.sleep(3) # Aguarda transição

            # Tira screenshot
            output_path = "assets/detective_screenshot.png"
            page.screenshot(path=output_path)
            print(f"Screenshot salva em: {output_path}")

        except Exception as e:
            print(f"Erro ao navegar/capturar: {e}")
            # Tira screenshot de onde estiver para debug
            page.screenshot(path="assets/debug_screenshot.png")
            print("Screenshot de debug salva.")

        browser.close()

if __name__ == "__main__":
    capture()
