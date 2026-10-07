---
name: ode-motion
description: Implementar movimentos no Stage e arte HTML em HyperFrames vinculados à fala, com composição determinística.
---

# ode-motion

Leia [motion](../../docs/editorial-motion-library.md), [contrato HyperFrames](../../docs/hyperframes-production.md) e frame.md. Declare operações com dados; tratamento não executa conta. Valores finais são exatos, sem contador inventado. Flow exige relação; reframe exige movimento/câmera.

Arte autoral HyperFrames fica em video/hyperframes/<nome>/index.html no Git. O worker injeta window.ODE com duração, fps, beats resolvidos e estados declarados. Uma timeline pausada registrada com id ode recebe seek arbitrário. Sem relógio, aleatoriedade não fixada, network, voz ou dados factuais desenhados como imagem. Assets/scripts locais.

Use estados por âncora e transições que preservem o objeto. Texto/contas/câmera/legendas ficam no Stage auditado. O clipe é preparado depois do alinhamento, tem fps/frames exatos e falha se não for auditável. Mudança visual não pede nova voz. Verifique contrato, clipe e MP4 final.
