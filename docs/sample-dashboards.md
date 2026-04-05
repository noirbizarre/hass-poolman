---
icon: lucide/layout-dashboard
---

# Sample Dashboards

This page provides two ready-to-use dashboard configurations for
Pool Manager. Copy the YAML into a
[manual Lovelace dashboard](https://www.home-assistant.io/dashboards/)
and replace every occurrence of `{pool}` with your pool's entity name
slug (e.g. `my_pool`).

Both dashboards are included in the [demo environment](../README.md) and
can be tested with `docker compose up`.

## Built-in Cards Dashboard

This dashboard uses **only standard Home Assistant cards** -- no custom
cards or HACS installations required.

### Built-in Sections

| Section | Cards used | What it shows |
| --- | --- | --- |
| Pool Status | `tile`, `gauge` | Pool mode, water quality, swimming safe, action required, quality score |
| Chemistry Readings | `sensor` (with graph), `tile` (status grid), `history-graph` | Temperature, pH, ORP readings with colored status indicators |
| Recommendations | `entities`, `markdown` | Active recommendation count and detailed action list |
| Filtration Control | `entities`, `tile`, `button`, `history-graph` | Filtration switch, duration, start time, mode, boost presets, pump history |
| Treatments | `tile`, `markdown` | Active treatments, safe-to-swim time, treatment details table |
| Activity Log | `logbook` | Recent measurements, treatments, and filtration events |
| Activation Wizard | `conditional`, `tile`, `markdown`, `button` | Activation step progress and confirm buttons (only visible in activating mode) |
| Quick Actions | `button` | Record measures, add treatments |

### Built-in YAML

??? example "Full YAML -- click to expand"

    Replace `{pool}` with your pool name slug (e.g. `my_pool`).

    ```yaml
    title: Pool Manager
    views:
      - title: Pool
        icon: mdi:pool
        cards:
          # ── Pool Status ──────────────────────────────────────────
          - type: heading
            heading: Pool Status
            heading_style: title
            icon: mdi:pool

          - type: grid
            columns: 2
            square: false
            cards:
              - type: tile
                entity: select.{pool}_pool_mode
                name: Pool Mode
                icon: mdi:pool
              - type: tile
                entity: binary_sensor.{pool}_action_required
                name: Action Required

          - type: grid
            columns: 2
            square: false
            cards:
              - type: tile
                entity: binary_sensor.{pool}_water_ok
                name: Water Quality
                color: green
              - type: tile
                entity: binary_sensor.{pool}_swimming_safe
                name: Swimming Safe
                color: cyan

          - type: gauge
            entity: sensor.{pool}_water_quality_score
            name: Water Quality Score
            min: 0
            max: 100
            needle: true
            severity:
              green: 80
              yellow: 50
              red: 0

          # ── Chemistry Readings ───────────────────────────────────
          - type: heading
            heading: Chemistry Readings
            heading_style: title
            icon: mdi:flask

          - type: grid
            columns: 3
            square: false
            cards:
              - type: sensor
                entity: sensor.{pool}_water_temperature
                name: Temperature
                graph: line
              - type: sensor
                entity: sensor.{pool}_ph
                name: pH
                graph: line
              - type: sensor
                entity: sensor.{pool}_orp
                name: ORP
                graph: line

          - type: grid
            columns: 5
            square: false
            cards:
              - type: tile
                entity: sensor.{pool}_ph_status
                name: pH
                vertical: true
              - type: tile
                entity: sensor.{pool}_orp_status
                name: ORP
                vertical: true
              - type: tile
                entity: sensor.{pool}_tac_status
                name: TAC
                vertical: true
              - type: tile
                entity: sensor.{pool}_cya_status
                name: CYA
                vertical: true
              - type: tile
                entity: sensor.{pool}_hardness_status
                name: Hardness
                vertical: true

          - type: history-graph
            title: Chemistry History (24h)
            hours_to_show: 24
            entities:
              - entity: sensor.{pool}_water_temperature
                name: Temperature
              - entity: sensor.{pool}_ph
                name: pH
              - entity: sensor.{pool}_orp
                name: ORP

          # ── Recommendations ──────────────────────────────────────
          - type: heading
            heading: Recommendations
            heading_style: title
            icon: mdi:clipboard-check

          - type: entities
            entities:
              - entity: sensor.{pool}_recommendations
                name: Active Recommendations
                icon: mdi:clipboard-list
              - entity: sensor.{pool}_chemistry_actions
                name: Chemistry Actions
                icon: mdi:beaker-check
              - entity: binary_sensor.{pool}_action_required
                name: Action Required

          - type: markdown
            title: Current Recommendations
            content: >
              {% set recs = state_attr('sensor.{pool}_recommendations', 'actions') %}
              {% if recs and recs | length > 0 %}
              {% for action in recs %}
              - {{ action }}
              {% endfor %}
              {% else %}
              No recommendations at this time.
              {% endif %}

          # ── Filtration Control ───────────────────────────────────
          - type: heading
            heading: Filtration Control
            heading_style: title
            icon: mdi:pump

          - type: entities
            entities:
              - entity: switch.{pool}_filtration_control
                name: Automatic Filtration
              - entity: sensor.{pool}_filtration_duration
                name: Recommended Duration
              - entity: select.{pool}_filtration_duration_mode
                name: Duration Mode
              - entity: number.{pool}_filtration_duration
                name: Duration Setting
              - entity: time.{pool}_filtration_start_time
                name: Start Time

          - type: grid
            columns: 2
            square: false
            cards:
              - type: tile
                entity: select.{pool}_filtration_boost
                name: Boost
                icon: mdi:rocket-launch
              - type: tile
                entity: sensor.{pool}_filtration_boost_remaining
                name: Boost Remaining

          - type: grid
            columns: 5
            square: false
            cards:
              - type: button
                name: Cancel
                icon: mdi:cancel
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: select.select_option
                  target:
                    entity_id: select.{pool}_filtration_boost
                  data:
                    option: "none"
              - type: button
                name: +2h
                icon: mdi:numeric-2
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: select.select_option
                  target:
                    entity_id: select.{pool}_filtration_boost
                  data:
                    option: "2"
              - type: button
                name: +4h
                icon: mdi:numeric-4
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: select.select_option
                  target:
                    entity_id: select.{pool}_filtration_boost
                  data:
                    option: "4"
              - type: button
                name: +8h
                icon: mdi:numeric-8
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: select.select_option
                  target:
                    entity_id: select.{pool}_filtration_boost
                  data:
                    option: "8"
              - type: button
                name: +24h
                icon: mdi:hours-24
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: select.select_option
                  target:
                    entity_id: select.{pool}_filtration_boost
                  data:
                    option: "24"

          - type: history-graph
            title: Filtration History (24h)
            hours_to_show: 24
            entities:
              - entity: switch.{pool}_filtration_control
                name: Filtration

          # ── Treatments ──────────────────────────────────────────
          - type: heading
            heading: Treatments
            heading_style: title
            icon: mdi:bottle-tonic-plus

          - type: grid
            columns: 2
            square: false
            cards:
              - type: tile
                entity: sensor.{pool}_active_treatments
                name: Active Treatments
                icon: mdi:bottle-tonic
              - type: tile
                entity: sensor.{pool}_safe_at
                name: Safe to Swim At
                icon: mdi:clock-check

          - type: markdown
            title: Active Treatments
            content: >
              {% set treats = state_attr('sensor.{pool}_active_treatments', 'treatments') %}
              {% if treats and treats | length > 0 %}
              | Product | Applied | Safe at | Quantity |
              | ------- | ------- | ------- | -------- |
              {% for t in treats %}
              | {{ t.product }} | {{ t.applied_at }} | {{ t.safe_at }} | {{ t.quantity_g }}g |
              {% endfor %}
              {% else %}
              No active treatments.
              {% endif %}

          # ── Activity Log ─────────────────────────────────────────
          - type: heading
            heading: Activity Log
            heading_style: title
            icon: mdi:history

          - type: logbook
            hours_to_show: 48
            entities:
              - event.{pool}_ph_measurement
              - event.{pool}_orp_measurement
              - event.{pool}_tac_measurement
              - event.{pool}_cya_measurement
              - event.{pool}_hardness_measurement
              - event.{pool}_temperature_measurement
              - event.{pool}_ph_minus_treatment
              - event.{pool}_ph_plus_treatment
              - event.{pool}_shock_chlorine_treatment
              - event.{pool}_chlorine_tablet_treatment
              - event.{pool}_filtration

          # ── Activation Wizard (visible only in activating mode) ─
          - type: conditional
            conditions:
              - condition: state
                entity: select.{pool}_pool_mode
                state: activating
            card:
              type: vertical-stack
              cards:
                - type: heading
                  heading: Activation Wizard
                  heading_style: title
                  icon: mdi:wizard-hat

                - type: grid
                  columns: 2
                  square: false
                  cards:
                    - type: tile
                      entity: sensor.{pool}_activation_step
                      name: Current Step
                      icon: mdi:wizard-hat
                    - type: tile
                      entity: select.{pool}_pool_mode
                      name: Pool Mode
                      icon: mdi:progress-wrench

                - type: markdown
                  title: Activation Progress
                  content: >
                    {% set progress = state_attr('sensor.{pool}_activation_step', 'progress') %}
                    {% set completed = state_attr('sensor.{pool}_activation_step', 'completed_steps') %}
                    {% set pending = state_attr('sensor.{pool}_activation_step', 'pending_steps') %}
                    **Progress:** {{ progress if progress else '0/5' }}

                    {% if completed %}
                    {% for step in completed %}
                    - ✅ {{ step | replace('_', ' ') | title }}
                    {% endfor %}
                    {% endif %}
                    {% if pending %}
                    {% for step in pending %}
                    - ⬜ {{ step | replace('_', ' ') | title }}
                    {% endfor %}
                    {% endif %}

                - type: grid
                  columns: 3
                  square: false
                  cards:
                    - type: button
                      name: Remove Cover
                      icon: mdi:umbrella-beach
                      show_name: true
                      show_icon: true
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: remove_cover
                        target: {}
                    - type: button
                      name: Raise Water
                      icon: mdi:water-plus
                      show_name: true
                      show_icon: true
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: raise_water_level
                        target: {}
                    - type: button
                      name: Clean Pool
                      icon: mdi:broom
                      show_name: true
                      show_icon: true
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: clean_pool_and_filter
                        target: {}

          # ── Quick Actions ───────────────────────────────────────
          - type: heading
            heading: Quick Actions
            heading_style: title
            icon: mdi:lightning-bolt

          - type: grid
            columns: 2
            square: false
            cards:
              - type: button
                name: Record Measure
                icon: mdi:test-tube
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: poolman.record_measure
                  data:
                    device_id: this
                    parameter: ph
                    value: 7.2
                  target: {}
                  confirmation:
                    text: >-
                      Record a pH measurement of 7.2?
                      Edit the value in the action data if needed.
              - type: button
                name: Add Treatment
                icon: mdi:bottle-tonic-plus
                show_name: true
                show_icon: true
                tap_action:
                  action: perform-action
                  perform_action: poolman.add_treatment
                  data:
                    device_id: this
                    product: galet_chlore
                    quantity_g: 200
                  target: {}
                  confirmation:
                    text: >-
                      Add a chlorine tablet treatment (200g)?
                      Edit the action data to change product or quantity.
    ```

!!! tip "Adapting the quick actions"

    The button cards call services with pre-filled sample parameters
    (pH 7.2 for measurement, chlorine tablet 200g for treatment) and
    show a confirmation dialog before executing. Edit the `data`
    section of each button's `tap_action` to change the default
    parameter, value, product, or quantity to match your workflow.

---

## Custom Cards Dashboard

This dashboard uses community custom cards for a more polished look,
inspired by the
[iopool custom card](https://docs.page/mguyard/hass-iopool/integration/custom-card).

### Prerequisites

Install the following custom cards via [HACS](https://hacs.xyz/):

| Card | Repository | Purpose |
| ---- | ---------- | ------- |
| [Bubble Card](https://github.com/Clooos/Bubble-Card) | `Clooos/Bubble-Card` | Entity display, separators, sub-buttons (chips), pop-up overlays |
| [button-card](https://github.com/custom-cards/button-card) | `custom-cards/button-card` | Highly customizable buttons with conditional styling |
| [mini-graph-card](https://github.com/kalkih/mini-graph-card) | `kalkih/mini-graph-card` | Animated line charts with color thresholds |
| [Pool Monitor Card](https://github.com/wilsto/pool-monitor-card) | `wilsto/pool-monitor-card` | Chemistry gauge display with setpoints |

### Custom Card Sections

| Section | Cards used | What it shows |
| ------- | ---------- | ------------- |
| Header | Bubble separator | Dashboard title |
| Pool Status | button-card, Bubble sub-buttons | Pool mode with colored icons, action required indicator, safety status chips |
| Water Quality | Bubble button, Pool Monitor Card | Quality score, chemistry gauges with setpoints |
| Temperature | mini-graph-card | 48h animated temperature graph with color thresholds |
| Chemistry Status | Bubble button (grid) | 5 status indicators |
| Recommendations | Bubble button, markdown | Recommendation count, detailed list |
| Filtration | button-card, Bubble button/sub-buttons, history-graph | Pump toggle, duration, mode, boost presets as sub-buttons, pump history |
| Treatments | Bubble button | Active treatment count |
| Activity Log | logbook | Recent measurements, treatments, and filtration events |
| Activation Wizard | `conditional`, Bubble separator/button, markdown, button-card | Activation step progress and confirm buttons (only visible in activating mode) |
| Quick Actions | Bubble button (grid) | Open Record Measure and Add Treatment pop-ups |
| Record Measure | Bubble pop-up, button-card (grid) | Pop-up with buttons for each measurement parameter (pH, ORP, TAC, CYA, hardness, temperature) |
| Add Treatment | Bubble pop-up, button-card (grid) | Pop-up with buttons for common treatments (chlorine, pH, anti-algae, flocculant) |

### Custom Card YAML

??? example "Full YAML -- click to expand"

    Replace `{pool}` with your pool name slug (e.g. `my_pool`).

    ```yaml
    title: Pool Manager
    views:
      - title: Pool
        icon: mdi:pool
        cards:
          # ── Header ──────────────────────────────────────────────
          - type: custom:bubble-card
            card_type: separator
            name: Pool Manager
            icon: mdi:pool

          # ── Pool Status & Mode ──────────────────────────────────
          - type: grid
            columns: 2
            square: false
            cards:
              - type: custom:button-card
                name: Pool Mode
                icon: mdi:pool
                entity: select.{pool}_pool_mode
                show_state: true
                state:
                  - value: active
                    icon: mdi:white-balance-sunny
                    styles:
                      img_cell:
                        - background: var(--green-color, #4caf50)
                  - value: hibernating
                    icon: mdi:snowflake
                    styles:
                      img_cell:
                        - background: var(--blue-color, #2196f3)
                  - value: winter_active
                    icon: mdi:sun-snowflake-variant
                    styles:
                      img_cell:
                        - background: var(--blue-color, #2196f3)
                  - value: winter_passive
                    icon: mdi:snowflake-alert
                    styles:
                      img_cell:
                        - background: var(--info-color, #039be5)
                  - value: activating
                    icon: mdi:progress-wrench
                    styles:
                      img_cell:
                        - background: var(--warning-color, #ff9800)
                styles:
                  grid:
                    - grid-template-areas: '"n" "s" "i"'
                    - grid-template-rows: min-content min-content 1fr
                  img_cell:
                    - justify-content: center
                    - width: 80px
                    - height: 80px
                    - margin: 8px auto
                    - background: var(--primary-color)
                    - border-radius: 50%
                  icon:
                    - width: 40px
                    - color: white
                  card:
                    - height: 100%
                    - padding: 16px
                  name:
                    - font-size: 16px
                    - font-weight: 500
                  state:
                    - font-size: 14px
                    - opacity: "0.7"
                    - text-transform: capitalize
                tap_action:
                  action: more-info

              - type: custom:button-card
                name: Actions Required
                icon: mdi:check-circle-outline
                entity: binary_sensor.{pool}_action_required
                show_state: true
                state:
                  - value: "off"
                    icon: mdi:check-circle-outline
                    styles:
                      img_cell:
                        - background: var(--green-color, #4caf50)
                  - value: "on"
                    icon: mdi:alert-circle
                    styles:
                      img_cell:
                        - background: var(--error-color, #db4437)
                styles:
                  grid:
                    - grid-template-areas: '"n" "s" "i"'
                    - grid-template-rows: min-content min-content 1fr
                  img_cell:
                    - justify-content: center
                    - width: 80px
                    - height: 80px
                    - margin: 8px auto
                    - background: var(--green-color, #4caf50)
                    - border-radius: 50%
                  icon:
                    - width: 40px
                    - color: white
                  card:
                    - height: 100%
                    - padding: 16px
                  name:
                    - font-size: 16px
                    - font-weight: 500
                  state:
                    - font-size: 14px
                    - opacity: "0.7"
                    - text-transform: capitalize
                tap_action:
                  action: more-info

          # ── Water Quality Score ──────────────────────────────────
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: sensor.{pool}_water_quality_score
            name: Water Quality Score
            icon: mdi:water-check
            show_state: true

          # ── Safety Status ────────────────────────────────────────
          - type: custom:bubble-card
            card_type: sub-buttons
            hide_main_background: true
            sub_button:
              - entity: binary_sensor.{pool}_water_ok
                name: Water OK
                icon: mdi:water-check
                show_state: true
                show_name: true
              - entity: binary_sensor.{pool}_swimming_safe
                name: Swimming
                icon: mdi:swim
                show_state: true
                show_name: true
              - entity: sensor.{pool}_active_treatments
                name: Treatments
                icon: mdi:bottle-tonic
                show_state: true
                show_name: true

          # ── Temperature Graph ────────────────────────────────────
          - type: custom:mini-graph-card
            entities:
              - entity: sensor.{pool}_water_temperature
                name: Water Temperature
            hours_to_show: 48
            animate: true
            line_width: 4
            group_by: hour
            hour24: true
            decimals: 1
            show:
              extrema: true
              average: true
              labels: false
            color_thresholds:
              - value: 18
                color: "#2196f3"
              - value: 24
                color: "#4caf50"
              - value: 28
                color: "#ff9800"
              - value: 32
                color: "#f44336"

          # ── Pool Monitor Card (Chemistry Gauges) ─────────────────
          - type: custom:pool-monitor-card
            title: Water Chemistry
            display:
              show_labels: true
              show_last_updated: true
              gradient: true
              language: en
            sensors:
              temperature:
                - entity: sensor.{pool}_water_temperature
                  setpoint: 27
                  step: 4
              ph:
                - entity: sensor.{pool}_ph
                  setpoint: 7.2
                  step: 0.3
              orp:
                - entity: sensor.{pool}_orp
                  setpoint: 750
                  step: 75

          # ── Chemistry Status ─────────────────────────────────────
          - type: grid
            columns: 5
            square: false
            cards:
              - type: custom:bubble-card
                card_type: button
                button_type: state
                entity: sensor.{pool}_ph_status
                name: pH
                icon: mdi:ph
                show_state: true
              - type: custom:bubble-card
                card_type: button
                button_type: state
                entity: sensor.{pool}_orp_status
                name: ORP
                icon: mdi:flash-triangle-outline
                show_state: true
              - type: custom:bubble-card
                card_type: button
                button_type: state
                entity: sensor.{pool}_tac_status
                name: TAC
                icon: mdi:beaker-outline
                show_state: true
              - type: custom:bubble-card
                card_type: button
                button_type: state
                entity: sensor.{pool}_cya_status
                name: CYA
                icon: mdi:shield-sun-outline
                show_state: true
              - type: custom:bubble-card
                card_type: button
                button_type: state
                entity: sensor.{pool}_hardness_status
                name: Hardness
                icon: mdi:water-opacity
                show_state: true

          # ── Recommendations ──────────────────────────────────────
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: sensor.{pool}_recommendations
            name: Recommendations
            icon: mdi:clipboard-check
            show_state: true
            button_action:
              tap_action:
                action: more-info

          - type: markdown
            content: >
              {% set recs = state_attr('sensor.{pool}_recommendations', 'actions') %}
              {% if recs and recs | length > 0 %}
              {% for action in recs %}
              - {{ action }}
              {% endfor %}
              {% else %}
              *No recommendations at this time.*
              {% endif %}

          # ── Filtration Control ───────────────────────────────────
          - type: grid
            columns: 2
            square: false
            cards:
              - type: custom:button-card
                entity: switch.{pool}_filtration_control
                name: Filtration
                icon: mdi:pump
                show_state: true
                tap_action:
                  action: toggle
                state:
                  - value: "on"
                    icon: mdi:pump
                    styles:
                      card:
                        - background: var(--green-color, #4caf50)
                      icon:
                        - color: white
                      name:
                        - color: white
                      state:
                        - color: white
                  - value: "off"
                    icon: mdi:pump-off
                    styles:
                      card:
                        - background: var(--error-color, #db4437)
                      icon:
                        - color: white
                      name:
                        - color: white
                      state:
                        - color: white
                styles:
                  card:
                    - padding: 16px
                    - height: 100%
                  icon:
                    - width: 36px
                  name:
                    - font-size: 16px
                    - font-weight: 500
                  state:
                    - font-size: 14px
                    - text-transform: capitalize

              - type: vertical-stack
                cards:
                  - type: custom:bubble-card
                    card_type: button
                    button_type: state
                    entity: sensor.{pool}_filtration_duration
                    name: Recommended
                    icon: mdi:clock-outline
                    show_state: true
                  - type: custom:bubble-card
                    card_type: button
                    button_type: state
                    entity: time.{pool}_filtration_start_time
                    name: Start Time
                    icon: mdi:clock-start
                    show_state: true
                  - type: custom:bubble-card
                    card_type: button
                    button_type: state
                    entity: select.{pool}_filtration_duration_mode
                    name: Mode
                    icon: mdi:cog
                    show_state: true

          # ── Filtration Boost (sub-buttons) ───────────────────────
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: select.{pool}_filtration_boost
            name: Filtration Boost
            icon: mdi:rocket-launch
            show_state: true
            sub_button:
              - name: "Off"
                icon: mdi:cancel
                tap_action:
                  action: call-service
                  service: select.select_option
                  data:
                    option: "none"
                  target:
                    entity_id: select.{pool}_filtration_boost
              - name: "+2h"
                icon: mdi:numeric-2
                tap_action:
                  action: call-service
                  service: select.select_option
                  data:
                    option: "2"
                  target:
                    entity_id: select.{pool}_filtration_boost
              - name: "+4h"
                icon: mdi:numeric-4
                tap_action:
                  action: call-service
                  service: select.select_option
                  data:
                    option: "4"
                  target:
                    entity_id: select.{pool}_filtration_boost
              - name: "+8h"
                icon: mdi:numeric-8
                tap_action:
                  action: call-service
                  service: select.select_option
                  data:
                    option: "8"
                  target:
                    entity_id: select.{pool}_filtration_boost
              - name: "24h"
                icon: mdi:hours-24
                tap_action:
                  action: call-service
                  service: select.select_option
                  data:
                    option: "24"
                  target:
                    entity_id: select.{pool}_filtration_boost

          - type: history-graph
            title: Filtration History (24h)
            hours_to_show: 24
            entities:
              - entity: switch.{pool}_filtration_control
                name: Filtration

          # ── Treatments ──────────────────────────────────────────
          - type: custom:bubble-card
            card_type: button
            button_type: state
            entity: sensor.{pool}_active_treatments
            name: Active Treatments
            icon: mdi:bottle-tonic-plus
            show_state: true
            button_action:
              tap_action:
                action: more-info

          # ── Activity Log ─────────────────────────────────────────
          - type: custom:bubble-card
            card_type: separator
            name: Activity Log
            icon: mdi:history

          - type: logbook
            hours_to_show: 48
            entities:
              - event.{pool}_ph_measurement
              - event.{pool}_orp_measurement
              - event.{pool}_tac_measurement
              - event.{pool}_cya_measurement
              - event.{pool}_hardness_measurement
              - event.{pool}_temperature_measurement
              - event.{pool}_ph_minus_treatment
              - event.{pool}_ph_plus_treatment
              - event.{pool}_shock_chlorine_treatment
              - event.{pool}_chlorine_tablet_treatment
              - event.{pool}_filtration

          # ── Activation Wizard (visible only in activating mode) ─
          - type: conditional
            conditions:
              - condition: state
                entity: select.{pool}_pool_mode
                state: activating
            card:
              type: vertical-stack
              cards:
                - type: custom:bubble-card
                  card_type: separator
                  name: Activation Wizard
                  icon: mdi:wizard-hat

                - type: custom:bubble-card
                  card_type: button
                  button_type: state
                  entity: sensor.{pool}_activation_step
                  name: Current Step
                  icon: mdi:wizard-hat
                  show_state: true
                  button_action:
                    tap_action:
                      action: more-info

                - type: markdown
                  content: >
                    {% set completed = state_attr('sensor.{pool}_activation_step', 'completed_steps') %}
                    {% set pending = state_attr('sensor.{pool}_activation_step', 'pending_steps') %}
                    {% if completed %}
                    {% for step in completed %}
                    - ✅ {{ step | replace('_', ' ') | title }}
                    {% endfor %}
                    {% endif %}
                    {% if pending %}
                    {% for step in pending %}
                    - ⬜ {{ step | replace('_', ' ') | title }}
                    {% endfor %}
                    {% endif %}

                - type: grid
                  columns: 3
                  square: true
                  cards:
                    - type: custom:button-card
                      name: Remove Cover
                      icon: mdi:umbrella-beach
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: remove_cover
                      styles:
                        card:
                          - padding: 12px
                        icon:
                          - width: 32px
                        name:
                          - font-size: 12px

                    - type: custom:button-card
                      name: Raise Water
                      icon: mdi:water-plus
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: raise_water_level
                      styles:
                        card:
                          - padding: 12px
                        icon:
                          - width: 32px
                        name:
                          - font-size: 12px

                    - type: custom:button-card
                      name: Clean Pool
                      icon: mdi:broom
                      tap_action:
                        action: perform-action
                        perform_action: poolman.confirm_activation_step
                        data:
                          device_id: this
                          step: clean_pool_and_filter
                      styles:
                        card:
                          - padding: 12px
                        icon:
                          - width: 32px
                        name:
                          - font-size: 12px

          # ── Quick Actions ───────────────────────────────────────
          - type: grid
            columns: 2
            square: false
            cards:
              - type: custom:bubble-card
                card_type: button
                button_type: name
                name: Record Measure
                icon: mdi:test-tube
                button_action:
                  tap_action:
                    action: navigate
                    navigation_path: "#record-measure"

              - type: custom:bubble-card
                card_type: button
                button_type: name
                name: Add Treatment
                icon: mdi:bottle-tonic-plus
                button_action:
                  tap_action:
                    action: navigate
                    navigation_path: "#add-treatment"

          # ── Popups ──────────────────────────────────────────────

          # Record Measure popup
          - type: vertical-stack
            cards:
              - type: custom:bubble-card
                card_type: pop-up
                hash: "#record-measure"
                name: Record Measure
                icon: mdi:test-tube
              - type: grid
                columns: 2
                square: false
                cards:
                  - type: custom:button-card
                    name: pH (7.2)
                    icon: mdi:ph
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: ph
                        value: 7.2
                      confirmation:
                        text: "Record a pH measurement of 7.2?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                  - type: custom:button-card
                    name: ORP (750 mV)
                    icon: mdi:flash-triangle-outline
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: orp
                        value: 750
                      confirmation:
                        text: "Record an ORP measurement of 750 mV?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                  - type: custom:button-card
                    name: TAC (150)
                    icon: mdi:beaker-outline
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: tac
                        value: 150
                      confirmation:
                        text: "Record an alkalinity (TAC) measurement of 150 ppm?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                  - type: custom:button-card
                    name: CYA (30)
                    icon: mdi:shield-sun-outline
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: cya
                        value: 30
                      confirmation:
                        text: "Record a cyanuric acid (CYA) measurement of 30 ppm?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                  - type: custom:button-card
                    name: Hardness (250)
                    icon: mdi:water-opacity
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: hardness
                        value: 250
                      confirmation:
                        text: "Record a calcium hardness measurement of 250 ppm?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                  - type: custom:button-card
                    name: Temp (27°C)
                    icon: mdi:thermometer-water
                    tap_action:
                      action: perform-action
                      perform_action: poolman.record_measure
                      data:
                        device_id: this
                        parameter: temperature
                        value: 27
                      confirmation:
                        text: "Record a water temperature of 27°C?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px

          # Add Treatment popup
          - type: vertical-stack
            cards:
              - type: custom:bubble-card
                card_type: pop-up
                hash: "#add-treatment"
                name: Add Treatment
                icon: mdi:bottle-tonic-plus
              - type: grid
                columns: 2
                square: false
                cards:
                  - type: custom:button-card
                    name: Chlorine Tablet
                    icon: mdi:circle-outline
                    label: "200 g"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: galet_chlore
                        quantity_g: 200
                      confirmation:
                        text: "Add a chlorine tablet treatment (200 g)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
                  - type: custom:button-card
                    name: Shock Chlorine
                    icon: mdi:flash
                    label: "300 g"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: chlore_choc
                        quantity_g: 300
                      confirmation:
                        text: "Add a shock chlorine treatment (300 g)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
                  - type: custom:button-card
                    name: pH Minus
                    icon: mdi:arrow-down-bold
                    label: "100 g"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: ph_minus
                        quantity_g: 100
                      confirmation:
                        text: "Add a pH minus treatment (100 g)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
                  - type: custom:button-card
                    name: pH Plus
                    icon: mdi:arrow-up-bold
                    label: "100 g"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: ph_plus
                        quantity_g: 100
                      confirmation:
                        text: "Add a pH plus treatment (100 g)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
                  - type: custom:button-card
                    name: Anti-algae
                    icon: mdi:leaf-off
                    label: "200 ml"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: anti_algae
                        quantity_g: 200
                      confirmation:
                        text: "Add an anti-algae treatment (200 ml)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
                  - type: custom:button-card
                    name: Flocculant
                    icon: mdi:filter-outline
                    label: "100 ml"
                    show_label: true
                    tap_action:
                      action: perform-action
                      perform_action: poolman.add_treatment
                      data:
                        device_id: this
                        product: flocculant
                        quantity_g: 100
                      confirmation:
                        text: "Add a flocculant treatment (100 ml)?"
                    styles:
                      card:
                        - padding: 12px
                      icon:
                        - width: 32px
                      name:
                        - font-size: 14px
                      label:
                        - font-size: 12px
                        - opacity: "0.7"
    ```

!!! note "Custom card versions in the demo"

    The demo environment automatically downloads the **latest release**
    of each custom card from GitHub at startup.  To pin a specific
    version, edit the `CUSTOM_CARDS` mapping in `demo/setup.py`.

---

## Using the Demo

The [demo environment](../README.md) includes both dashboards
pre-configured. To try them out:

```bash
docker compose up
```

Once the setup completes, open:

- **Built-in dashboard:** <http://localhost:8123/pool-builtin/0>
- **Custom dashboard:** <http://localhost:8123/pool-custom/0>

Credentials: `admin` / `admin`

The demo also includes a **Sensor Controls** section at the bottom of
each dashboard where you can adjust the simulated sensor values
(temperature, pH, ORP, etc.) to see how the dashboard reacts in
real time.

## Customization Tips

- **Entity IDs:** Entity IDs are derived from the **translated entity
  name** in `strings.json`, not the internal `key`. For example, the
  temperature sensor's entity ID is `sensor.{pool}_water_temperature`
  (from the translated name "Water temperature"), not
  `sensor.{pool}_temperature`. See [Entities](entities.md) for the
  full list of available entities and their attributes.

- **Recommendations detail:** The `recommendations` sensor exposes an
  `actions` attribute (list of strings) that you can render with a
  `markdown` card using Jinja templates.

- **Chemistry status colors:** Each chemistry status sensor
  (`ph_status`, `orp_status`, etc.) returns `good`, `warning`, or `bad`.
  Use conditional styling to display green/orange/red indicators.

- **Filtration boost presets:** The `filtration_boost` select entity
  accepts `none`, `2`, `4`, `8`, and `24`. Wire these to
  Bubble Card sub-buttons or action cards for quick access.

- **Pop-ups:** Use Bubble Card's `pop-up` card type to create overlay
  forms for recording measures or adding treatments. Define the pop-up
  at the end of the view and trigger it with `navigation_path: "#hash"`.

- **Services:** Use the `poolman.record_measure`,
  `poolman.add_treatment`, `poolman.boost_filtration`, and
  `poolman.confirm_activation_step` services in button tap actions.
  See [Entities -- Events](entities.md#events) for required fields.
