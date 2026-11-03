#pragma once
// Entites generees automatiquement pour chaque lampe declaree dans le YAML
// (bloc `primary:` et liste `lamps:` de nightmatiq_mesh). Chaque classe lit
// l'etat du hub par adresse unicast et ne publie qu'en cas de changement,
// comme le faisaient les anciens capteurs template du YAML.

#include <cmath>
#include <string>

#include "esphome/core/component.h"
#include "esphome/components/binary_sensor/binary_sensor.h"
#include "esphome/components/button/button.h"
#include "esphome/components/number/number.h"
#include "esphome/components/select/select.h"
#include "esphome/components/sensor/sensor.h"
#include "esphome/components/switch/switch.h"
#include "esphome/components/text_sensor/text_sensor.h"

#include "nightmatiq_mesh.h"

namespace esphome {
namespace nightmatiq_mesh {

class LampChild {
 public:
  void set_parent(NightmatiqMesh *parent) { this->parent_ = parent; }
  void set_base(uint16_t base) { this->base_ = base; }

 protected:
  NightmatiqMesh *parent_{nullptr};
  uint16_t base_{0};
};

// ---------------------------------------------------------------- capteurs
enum class LampSensorKind : uint8_t {
  LUX,
  RSSI,
  HARDWARE,
  MOTION_LEVEL,          // lampe supplementaire
  PRIMARY_MOTION_LEVEL,  // lampe principale
};

class LampSensor : public sensor::Sensor, public PollingComponent, public LampChild {
 public:
  void set_kind(LampSensorKind kind) { this->kind_ = kind; }
  void update() override {
    float value = NAN;
    switch (this->kind_) {
      case LampSensorKind::LUX:
        value = this->parent_->lamp_lux(this->base_);
        break;
      case LampSensorKind::RSSI:
        value = this->parent_->lamp_rssi(this->base_);
        break;
      case LampSensorKind::HARDWARE:
        value = this->parent_->lamp_hardware(this->base_);
        break;
      case LampSensorKind::MOTION_LEVEL:
      case LampSensorKind::PRIMARY_MOTION_LEVEL: {
        const int raw = this->kind_ == LampSensorKind::MOTION_LEVEL ? this->parent_->lamp_motion(this->base_)
                                                                     : this->parent_->motion_raw();
        if (raw < 0 || raw == 0xFF)
          return;
        value = raw / 2.0f;
        break;
      }
    }
    if (std::isnan(value) || value == this->last_)
      return;
    this->last_ = value;
    this->publish_state(value);
  }

 protected:
  LampSensorKind kind_{LampSensorKind::LUX};
  float last_{NAN};
};

// ---------------------------------------------------------- binaires
enum class LampBinaryKind : uint8_t { OUTPUT, MOTION, PRIMARY_MOTION };

class LampBinarySensor : public binary_sensor::BinarySensor, public PollingComponent, public LampChild {
 public:
  void set_kind(LampBinaryKind kind) { this->kind_ = kind; }
  void update() override {
    switch (this->kind_) {
      case LampBinaryKind::OUTPUT: {
        const int v = this->parent_->lamp_output(this->base_);
        if (v >= 0)
          this->publish_state(v == 1);
        break;
      }
      case LampBinaryKind::MOTION:
      case LampBinaryKind::PRIMARY_MOTION: {
        const int v = this->kind_ == LampBinaryKind::MOTION ? this->parent_->lamp_motion(this->base_)
                                                             : this->parent_->motion_raw();
        if (v >= 0 && v != 0xFF)
          this->publish_state(v > 0);
        break;
      }
    }
  }

 protected:
  LampBinaryKind kind_{LampBinaryKind::OUTPUT};
};

// ------------------------------------------------------------- nombres
enum class LampNumberKind : uint8_t { LIGHTNESS, LC_PROP, THRESHOLD };

class LampNumber : public number::Number, public PollingComponent, public LampChild {
 public:
  void set_kind(LampNumberKind kind) { this->kind_ = kind; }
  void set_property(uint16_t property) { this->property_ = property; }
  void update() override {
    float value = NAN;
    switch (this->kind_) {
      case LampNumberKind::LIGHTNESS:
        value = this->parent_->lamp_lightness(this->base_);
        break;
      case LampNumberKind::LC_PROP:
        value = this->parent_->lamp_lc_prop(this->base_, this->property_);
        break;
      case LampNumberKind::THRESHOLD:
        value = this->parent_->lamp_threshold(this->base_);
        break;
    }
    if (std::isnan(value) || value == this->last_)
      return;
    this->last_ = value;
    this->publish_state(value);
  }

 protected:
  void control(float value) override {
    switch (this->kind_) {
      case LampNumberKind::LIGHTNESS:
        this->parent_->set_lamp_lightness(this->base_, value);
        break;
      case LampNumberKind::LC_PROP:
        this->parent_->set_lamp_lc_prop(this->base_, this->property_, value);
        break;
      case LampNumberKind::THRESHOLD:
        this->parent_->set_lamp_threshold(this->base_, value);
        break;
    }
    // Les setters du hub memorisent la valeur demandee : affichage immediat,
    // puis confirmation par la relecture Mesh.
    this->update();
  }

  LampNumberKind kind_{LampNumberKind::LIGHTNESS};
  uint16_t property_{0};
  float last_{NAN};
};

// Seuil de la lampe principale : publie par le hub, ecrit via set_threshold().
class PrimaryThresholdNumber : public number::Number, public Component, public LampChild {
 protected:
  void control(float value) override { this->parent_->set_threshold(value); }
};

// ------------------------------------------------------------- selects
static const char *const MODE_AUTO = "Auto";
static const char *const MODE_ON = "Always On";
static const char *const MODE_OFF = "Always Off";

class LampModeSelect : public select::Select, public PollingComponent, public LampChild {
 public:
  void update() override {
    const int lc = this->parent_->lamp_lc_mode(this->base_);
    const int out = this->parent_->lamp_output(this->base_);
    const char *value = nullptr;
    if (lc == 1)
      value = MODE_AUTO;
    else if (lc == 0 && out == 1)
      value = MODE_ON;
    else if (lc == 0 && out == 0)
      value = MODE_OFF;
    if (value == nullptr || value == this->last_)
      return;
    this->last_ = value;
    this->publish_state(value);
  }

 protected:
  void control(const std::string &value) override { this->parent_->set_lamp_mode(this->base_, value); }
  const char *last_{nullptr};
};

// Mode de la lampe principale : publie par le hub, ecrit via set_mode().
// Optimiste comme l'ancien select template (affichage immediat).
class PrimaryModeSelect : public select::Select, public Component, public LampChild {
 public:
  void setup() override {
    if (!this->has_state())
      this->publish_state(MODE_AUTO);
  }

 protected:
  void control(const std::string &value) override {
    this->parent_->set_mode(value);
    this->publish_state(value);
  }
};

// --------------------------------------------------------------- textes
enum class LampTextKind : uint8_t { FIRMWARE, CONSTANT };

class LampTextSensor : public text_sensor::TextSensor, public PollingComponent, public LampChild {
 public:
  void set_kind(LampTextKind kind) { this->kind_ = kind; }
  void set_constant(const std::string &value) { this->constant_ = value; }
  void update() override {
    const std::string value =
        this->kind_ == LampTextKind::FIRMWARE ? this->parent_->lamp_firmware(this->base_) : this->constant_;
    if (value.empty() || (this->has_state() && value == this->state))
      return;
    this->publish_state(value);
  }

 protected:
  LampTextKind kind_{LampTextKind::FIRMWARE};
  std::string constant_;
};

// ------------------------------------------------------- relais Mesh
class LampRelaySwitch : public switch_::Switch, public PollingComponent, public LampChild {
 public:
  void update() override {
    const int relay = this->parent_->lamp_relay(this->base_);
    if (relay == 0 || relay == 1)
      this->publish_state(relay == 1);
  }

 protected:
  // Pas d'etat optimiste : l'etat reel est publie au retour du Config Relay Status.
  void write_state(bool state) override { this->parent_->set_lamp_relay(this->base_, state); }
};

// -------------------------------------------------------------- boutons
enum class GatewayButtonKind : uint8_t { REFRESH, RELAY_REFRESH };

class GatewayButton : public button::Button, public Component, public LampChild {
 public:
  void set_kind(GatewayButtonKind kind) { this->kind_ = kind; }

 protected:
  void press_action() override {
    if (this->kind_ == GatewayButtonKind::REFRESH)
      this->parent_->request_refresh();
    else
      this->parent_->request_relay_refresh();
  }
  GatewayButtonKind kind_{GatewayButtonKind::REFRESH};
};

}  // namespace nightmatiq_mesh
}  // namespace esphome
