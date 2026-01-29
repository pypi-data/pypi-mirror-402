// Copyright 2021, Mycroft AI Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//    http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

import QtQuick 2.4
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.4
import org.kde.kirigami 2.4 as Kirigami
import QtGraphicalEffects 1.0
import Mycroft 1.0 as Mycroft

Mycroft.CardDelegate {
    id: root
    cardBackgroundOverlayColor: sessionData.colorHex

    Title {
        id: colorName
        anchors.bottom: colorHex.top
        anchors.topMargin: Mycroft.Units.gridUnit
        anchors.bottomMargin: Mycroft.Units.gridUnit * 6
        anchors.horizontalCenter: parent.horizontalCenter
        fontSize: Mycroft.Units.gridUnit * 6
        fontStyle: "Bold"
        textColor: sessionData.textColor
        heightUnits: 3
        text: sessionData.colorName
    }

    Title {
        id: colorHex
        anchors.topMargin: Mycroft.Units.gridUnit * 3
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        fontSize: Mycroft.Units.gridUnit * 3
        fontStyle: "Bold"
        textColor: sessionData.textColor
        heightUnits: 3
        text: sessionData.colorHex
    }

    Title {
        id: colorRGB
        anchors.top: colorHex.bottom
        anchors.topMargin: Mycroft.Units.gridUnit * 3
        anchors.horizontalCenter: parent.horizontalCenter
        fontSize: Mycroft.Units.gridUnit * 3
        fontStyle: "Bold"
        textColor: sessionData.textColor
        heightUnits: 3
        text: sessionData.colorRGB
    }

}
