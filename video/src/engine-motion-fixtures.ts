// Technical fixtures exercise different authored compositions. They are not
// examples for choosing a future episode's subject or storyboard.
export const engineMotionFixtures = [
  {
    id: "technical-flow", title: "Da peça à entrega", duration_frames: 300,
    visual: {
      stage: {show_title: false, camera_mode: "manual", motion_profile: "narrative", elements: [
        {id: "part", kind: "object", object_type: "component", svg_motion: "trace", label: "Componente", x: 5, y: 25, width: 22, height: 42, initially_visible: true},
        {id: "assembly", kind: "object", object_type: "factory", svg_motion: "assemble", label: "Montagem", x: 39, y: 25, width: 22, height: 42, initially_visible: false},
        {id: "delivery", kind: "object", object_type: "truck", svg_motion: "trace", label: "Entrega", x: 73, y: 25, width: 22, height: 42, initially_visible: false},
      ], connections: [{from: "part", to: "assembly", semantic: "sequence"}, {from: "assembly", to: "delivery", semantic: "sequence"}]},
      beats: [
        {target_id: "part", headline: "Componente", action: "focus", resolved_frame: 0, camera: {x: 22, y: 46, zoom: 1.35, motion_seconds: 1.1}},
        {target_id: "assembly", headline: "Montagem", action: "reveal", entrance: {style: "wipe", direction: "left"}, motion_seconds: .8, resolved_frame: 85, camera: {x: 50, y: 50, zoom: 1, motion_seconds: 1.2}},
        {target_id: "delivery", headline: "Entrega", action: "reveal", entrance: {style: "slide", direction: "left"}, motion_seconds: .65, resolved_frame: 160},
        {target_id: "delivery", headline: "Entrega", action: "focus", retire_ids: ["part"], moves: [{id: "delivery", x: 74, y: 20}], motion_seconds: 1.1, resolved_frame: 230, camera: {x: 67, y: 46, zoom: 1.2, motion_seconds: 1.5}},
      ],
    },
  },
  {
    id: "technical-equation", title: "Quantidade em uma demonstração", duration_frames: 300,
    visual: {
      stage: {show_title: false, camera_mode: "static", motion_profile: "narrative", elements: [
        {id: "title", kind: "label", label: "Uma conta construída na tela", x: 5, y: 3, width: 90, height: 16, initially_visible: false, label_size: 52},
        {id: "first", kind: "metric", label: "Grupo inicial", value: "12", x: 5, y: 32, width: 24, height: 39, initially_visible: true},
        {id: "added", kind: "metric", label: "Peças adicionadas", value: "3", x: 38, y: 32, width: 24, height: 39, initially_visible: false},
        {id: "result", kind: "metric", label: "Total no exemplo", value: "15", x: 71, y: 32, width: 24, height: 39, initially_visible: false},
        {id: "note", kind: "note", label: "Ensaio técnico · números ilustrativos", x: 5, y: 82, width: 90, height: 12, initially_visible: false},
      ], connections: []},
      beats: [
        {target_id: "title", headline: "Uma conta construída na tela", action: "reveal", treatment: "kinetic_type", motion_seconds: 1.2, resolved_frame: 0},
        {target_id: "added", headline: "Peças adicionadas", action: "reveal", entrance: {style: "scale"}, motion_seconds: .7, resolved_frame: 90},
        {target_id: "result", headline: "Total no exemplo", action: "reveal", treatment: "equation", motion_seconds: 1.15, operation: {kind: "equation", input_ids: ["first", "added"], operator: "+", result_id: "result"}, resolved_frame: 165},
        {target_id: "note", headline: "Ensaio técnico · números ilustrativos", action: "reveal", treatment: "masked_emphasis", motion_seconds: .8, resolved_frame: 240},
      ],
    },
  },
];
