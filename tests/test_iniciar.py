import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import iniciar


def preparar(monkeypatch, base, comandos, docker_desktop=True):
    """base: respuestas sucesivas de base_disponible. comandos: {"up"|"info": [resultados]}."""
    corridos = []
    monkeypatch.setattr(iniciar, "base_disponible", lambda: base.pop(0) if base else True)

    def ejecutar(comando, pausa):
        corridos.append(comando[1])
        return comandos[comando[1]].pop(0)

    monkeypatch.setattr(iniciar, "_ejecutar", ejecutar)
    monkeypatch.setattr(iniciar.os.path, "exists", lambda ruta: docker_desktop)
    monkeypatch.setattr(iniciar.subprocess, "Popen", lambda *a, **k: corridos.append("desktop"))
    monkeypatch.setattr(iniciar, "ESPERA_DOCKER", 0.05)
    monkeypatch.setattr(iniciar, "ESPERA_BASE", 0.05)
    error = iniciar.preparar_base(pausa=lambda segundos: None)
    return error, corridos


def test_con_la_base_levantada_no_toca_docker(monkeypatch):
    assert preparar(monkeypatch, [True], {}) == (None, [])


def test_levanta_la_base_si_docker_esta_abierto(monkeypatch):
    error, corridos = preparar(monkeypatch, [False, False, True], {"compose": [True]})
    assert error is None and corridos == ["compose"]


def test_abre_docker_desktop_si_esta_cerrado(monkeypatch):
    error, corridos = preparar(
        monkeypatch, [False, True], {"compose": [False, True], "info": [False, True]}
    )
    assert error is None
    assert corridos == ["compose", "desktop", "info", "info", "compose"]


def test_sin_docker_desktop_informa_el_motivo(monkeypatch):
    error, corridos = preparar(monkeypatch, [False], {"compose": [False]}, docker_desktop=False)
    assert "Docker Desktop" in error and corridos == ["compose"]


def test_informa_si_la_base_no_responde(monkeypatch):
    error, _ = preparar(monkeypatch, [False] * 10_000_000, {"compose": [True]})
    assert "no respondió" in error
