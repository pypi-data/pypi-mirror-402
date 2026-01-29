from __future__ import annotations
import typing
import wpilib._wpilib
import wpilib.interfaces._interfaces
import wpiutil._wpiutil
__all__: list[str] = ['CANVenom', 'TMD37003', 'TimeOfFlight']
class CANVenom(wpilib._wpilib.MotorSafety, wpilib.interfaces._interfaces.MotorController, wpiutil._wpiutil.Sendable):
    class BrakeCoastMode:
        """
        Members:
        
          kCoast
        
          kBrake
        """
        __members__: typing.ClassVar[dict[str, CANVenom.BrakeCoastMode]]  # value = {'kCoast': <BrakeCoastMode.kCoast: 0>, 'kBrake': <BrakeCoastMode.kBrake: 1>}
        kBrake: typing.ClassVar[CANVenom.BrakeCoastMode]  # value = <BrakeCoastMode.kBrake: 1>
        kCoast: typing.ClassVar[CANVenom.BrakeCoastMode]  # value = <BrakeCoastMode.kCoast: 0>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    class ControlMode:
        """
        Members:
        
          kDisabled
        
          kProportional
        
          kCurrentControl
        
          kSpeedControl
        
          kPositionControl
        
          kMotionProfile
        
          kFollowTheLeader
        
          kVoltageControl
        """
        __members__: typing.ClassVar[dict[str, CANVenom.ControlMode]]  # value = {'kDisabled': <ControlMode.kDisabled: 0>, 'kProportional': <ControlMode.kProportional: 1>, 'kCurrentControl': <ControlMode.kCurrentControl: 3>, 'kSpeedControl': <ControlMode.kSpeedControl: 4>, 'kPositionControl': <ControlMode.kPositionControl: 5>, 'kMotionProfile': <ControlMode.kMotionProfile: 6>, 'kFollowTheLeader': <ControlMode.kFollowTheLeader: 7>, 'kVoltageControl': <ControlMode.kVoltageControl: 8>}
        kCurrentControl: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kCurrentControl: 3>
        kDisabled: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kDisabled: 0>
        kFollowTheLeader: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kFollowTheLeader: 7>
        kMotionProfile: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kMotionProfile: 6>
        kPositionControl: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kPositionControl: 5>
        kProportional: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kProportional: 1>
        kSpeedControl: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kSpeedControl: 4>
        kVoltageControl: typing.ClassVar[CANVenom.ControlMode]  # value = <ControlMode.kVoltageControl: 8>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    class FaultFlag:
        """
        Members:
        
          kNone
        
          kNoHeartbeat
        
          kNoLeaderHeartbeat
        
          kBadLeaderID
        
          kHighTemperature
        
          kHighCurrent
        
          kBadMode
        
          kDuplicateID
        
          kForwardLimit
        
          kReverseLimit
        
          kReset
        """
        __members__: typing.ClassVar[dict[str, CANVenom.FaultFlag]]  # value = {'kNone': <FaultFlag.kNone: 0>, 'kNoHeartbeat': <FaultFlag.kNoHeartbeat: 1>, 'kNoLeaderHeartbeat': <FaultFlag.kNoLeaderHeartbeat: 2>, 'kBadLeaderID': <FaultFlag.kBadLeaderID: 4>, 'kHighTemperature': <FaultFlag.kHighTemperature: 8>, 'kHighCurrent': <FaultFlag.kHighCurrent: 16>, 'kBadMode': <FaultFlag.kBadMode: 32>, 'kDuplicateID': <FaultFlag.kDuplicateID: 64>, 'kForwardLimit': <FaultFlag.kForwardLimit: 128>, 'kReverseLimit': <FaultFlag.kReverseLimit: 256>, 'kReset': <FaultFlag.kReset: 512>}
        kBadLeaderID: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kBadLeaderID: 4>
        kBadMode: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kBadMode: 32>
        kDuplicateID: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kDuplicateID: 64>
        kForwardLimit: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kForwardLimit: 128>
        kHighCurrent: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kHighCurrent: 16>
        kHighTemperature: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kHighTemperature: 8>
        kNoHeartbeat: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kNoHeartbeat: 1>
        kNoLeaderHeartbeat: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kNoLeaderHeartbeat: 2>
        kNone: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kNone: 0>
        kReset: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kReset: 512>
        kReverseLimit: typing.ClassVar[CANVenom.FaultFlag]  # value = <FaultFlag.kReverseLimit: 256>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    class MotionProfileState:
        """
        Members:
        
          kInit
        
          kRunning
        
          kErrBufferCleared
        
          kErrBufferUnderflow
        
          kErrBufferInvalid
        
          kDone
        """
        __members__: typing.ClassVar[dict[str, CANVenom.MotionProfileState]]  # value = {'kInit': <MotionProfileState.kInit: 0>, 'kRunning': <MotionProfileState.kRunning: 1>, 'kErrBufferCleared': <MotionProfileState.kErrBufferCleared: 2>, 'kErrBufferUnderflow': <MotionProfileState.kErrBufferUnderflow: 3>, 'kErrBufferInvalid': <MotionProfileState.kErrBufferInvalid: 4>, 'kDone': <MotionProfileState.kDone: 5>}
        kDone: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kDone: 5>
        kErrBufferCleared: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kErrBufferCleared: 2>
        kErrBufferInvalid: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kErrBufferInvalid: 4>
        kErrBufferUnderflow: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kErrBufferUnderflow: 3>
        kInit: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kInit: 0>
        kRunning: typing.ClassVar[CANVenom.MotionProfileState]  # value = <MotionProfileState.kRunning: 1>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    def PIDWrite(self, output: typing.SupportsFloat) -> None:
        ...
    def __init__(self, motorID: typing.SupportsInt) -> None:
        ...
    def addMotionProfilePoint(self, time: typing.SupportsFloat, speed: typing.SupportsFloat, position: typing.SupportsFloat) -> None:
        ...
    def clearLatchedFaults(self) -> None:
        ...
    def clearMotionProfilePoints(self) -> None:
        ...
    def completeMotionProfilePath(self, time: typing.SupportsFloat, position: typing.SupportsFloat) -> None:
        ...
    def disable(self) -> None:
        ...
    def enable(self) -> None:
        ...
    def enableLimitSwitches(self, fwdLimitSwitchEnabled: bool, revLimitSwitchEnabled: bool) -> None:
        ...
    def executePath(self) -> None:
        ...
    def follow(self, leadVenom: CANVenom) -> None:
        ...
    def get(self) -> float:
        ...
    def getActiveControlMode(self) -> CANVenom.ControlMode:
        ...
    def getActiveFaults(self) -> CANVenom.FaultFlag:
        ...
    def getAuxVoltage(self) -> float:
        ...
    def getB(self) -> float:
        ...
    def getBrakeCoastMode(self) -> CANVenom.BrakeCoastMode:
        ...
    def getBusVoltage(self) -> float:
        ...
    def getControlMode(self) -> CANVenom.ControlMode:
        ...
    def getCurrentMotionProfilePoint(self) -> int:
        ...
    def getDescription(self) -> str:
        ...
    def getDutyCycle(self) -> float:
        ...
    def getFirmwareVersion(self) -> int:
        ...
    def getFwdLimitSwitchActive(self) -> bool:
        ...
    def getInverted(self) -> bool:
        ...
    def getKD(self) -> float:
        ...
    def getKF(self) -> float:
        ...
    def getKI(self) -> float:
        ...
    def getKP(self) -> float:
        ...
    def getLatchedFaults(self) -> CANVenom.FaultFlag:
        ...
    def getMaxAcceleration(self) -> float:
        ...
    def getMaxJerk(self) -> float:
        ...
    def getMaxPILimit(self) -> float:
        ...
    def getMaxSpeed(self) -> float:
        ...
    def getMinPILimit(self) -> float:
        ...
    def getMotionProfileIsValid(self) -> bool:
        ...
    def getMotionProfilePositionTarget(self) -> float:
        ...
    def getMotionProfileSpeedTarget(self) -> float:
        ...
    def getMotionProfileState(self) -> CANVenom.MotionProfileState:
        ...
    def getNumAvaliableMotionProfilePoints(self) -> int:
        ...
    def getOutputCurrent(self) -> float:
        ...
    def getOutputVoltage(self) -> float:
        ...
    def getPIDTarget(self) -> float:
        ...
    def getPosition(self) -> float:
        ...
    def getRevLimitSwitchActive(self) -> bool:
        ...
    def getSerialNumber(self) -> int:
        ...
    def getSpeed(self) -> float:
        ...
    def getTemperature(self) -> float:
        ...
    def identifyMotor(self) -> None:
        ...
    def initSendable(self, builder: wpiutil._wpiutil.SendableBuilder) -> None:
        ...
    def resetPosition(self) -> None:
        ...
    def set(self, command: typing.SupportsFloat) -> None:
        ...
    def setB(self, b: typing.SupportsFloat) -> None:
        ...
    def setBrakeCoastMode(self, brakeCoastMode: CANVenom.BrakeCoastMode) -> None:
        ...
    @typing.overload
    def setCommand(self, mode: CANVenom.ControlMode, command: typing.SupportsFloat) -> None:
        ...
    @typing.overload
    def setCommand(self, mode: CANVenom.ControlMode, command: typing.SupportsFloat, kF: typing.SupportsFloat, b: typing.SupportsFloat) -> None:
        ...
    def setControlMode(self, controlMode: CANVenom.ControlMode) -> None:
        ...
    def setInverted(self, isInverted: bool) -> None:
        ...
    def setKD(self, kD: typing.SupportsFloat) -> None:
        ...
    def setKF(self, kF: typing.SupportsFloat) -> None:
        ...
    def setKI(self, kI: typing.SupportsFloat) -> None:
        ...
    def setKP(self, kP: typing.SupportsFloat) -> None:
        ...
    def setMaxAcceleration(self, limit: typing.SupportsFloat) -> None:
        ...
    def setMaxJerk(self, limit: typing.SupportsFloat) -> None:
        ...
    def setMaxPILimit(self, limit: typing.SupportsFloat) -> None:
        ...
    def setMaxSpeed(self, limit: typing.SupportsFloat) -> None:
        ...
    def setMinPILimit(self, limit: typing.SupportsFloat) -> None:
        ...
    def setPID(self, kP: typing.SupportsFloat, kI: typing.SupportsFloat, kD: typing.SupportsFloat, kF: typing.SupportsFloat, b: typing.SupportsFloat) -> None:
        ...
    def setPosition(self, newPosition: typing.SupportsFloat) -> None:
        ...
    def stopMotor(self) -> None:
        ...
class TMD37003:
    def __init__(self, i2cPort: wpilib._wpilib.I2C.Port) -> None:
        """
        Create Instance of TMD3700 color sensor driver.
        
        :param i2cPort: Internal/MXP I2C port on the roboRIO
        """
    def configureColorSense(self, alsIntegrationTime: typing.SupportsFloat, alsGain: typing.SupportsInt) -> None:
        """
        Configure TMD3700 Color (Ambient Light Sensing) parameters.
        
        :param alsIntegrationTime: Color sensing sample time in milliseconds.  Value may
                                   range from 2.8 to 721ms.   Longer sample times act to
                                   filtered the sampled color.
        :param alsGain:            Color sensor gain as a value between 1 and 64.
        """
    def configureProximitySense(self, proximitySampleTime: typing.SupportsFloat, proximityPulseLength: typing.SupportsFloat, numProximityPulses: typing.SupportsInt, proximityGain: typing.SupportsInt, proximityLedCurrent: typing.SupportsInt) -> None:
        """
        Configure TMD3700 Proximity sense parameters.
        
        :param proximitySampleTime:  Proximity sensing sample time in milliseconds.  Value
                                     may range from 0.088 to 22.528 ms.
        :param proximityPulseLength: Lengh of each IR LED pulse during proximity measurement
                                     in milliseconds.  Value must fall between 0.004 and 0.032 ms.
        :param numProximityPulses:   Number of proximity IR LED pulses which occur during each
                                     sample period
        :param proximityGain:        Proximity sensor gain as a value between 1 and 8.
        :param proximityLedCurrent:  Proximity IR LED current in milliamps.  Value must fall
                                     between 6 and 192 mA
        """
    def getAmbientLightLevel(self) -> float:
        """
        Get clear (Ambient) channel value.
        
        :returns: Normalized clear channel value as ratio between 0 and 1.
        """
    def getBlue(self) -> float:
        """
        Get blue channel value.
        
        :returns: Normalized blue channel value as ratio between 0 and 1..
        """
    def getColor(self) -> wpilib._wpilib.Color:
        """
        Get gamma corrected RGB values from sensor
        
        :returns: Value of RGB samples
        """
    def getGreen(self) -> float:
        """
        Get green channel value.
        
        :returns: Normalized green channel value as ratio between 0 and 1..
        """
    def getHue(self) -> float:
        """
        Get the measured color (hue).
        
        :returns: Measured hue in degrees
        """
    def getProximity(self) -> float:
        """
        Get proximity value.
        
        :returns: Normalized proximity value as ratio between 0 and 1.
        """
    def getRed(self) -> float:
        """
        Get red channel value.
        
        :returns: Normalized red channel value as ratio between 0 and 1..
        """
    def getSaturation(self) -> float:
        """
        Get measured color saturation.
        
        :returns: Measured saturation as ratio between 0 and 1
        """
    def setGain(self, r: typing.SupportsFloat, g: typing.SupportsFloat, b: typing.SupportsFloat, c: typing.SupportsFloat, gamma: typing.SupportsFloat) -> None:
        """
        Specifiy gains and gamma value to convert raw RGB samples to normalized
        RGB values to aproximate sRGB space.
        
        The default gains are calibrated for the built in white LED.  If another
        lighting source is used this function may be required to specify the
        white point.
        
        Channels are calculated using:
        {Normilized value} = ({Raw value} * gain) ^ (1/gamma)
        
        :param r:     Red channel gain
        :param g:     Green channel gain
        :param b:     Blue channel gain
        :param c:     Clear (ambient) channel gain
        :param gamma: Gamma vaulke used to convert raw (linear) samples to something
                      that responds like a human eye
        """
class TimeOfFlight(wpiutil._wpiutil.Sendable):
    class RangingMode:
        """
        Members:
        
          kShort
        
          kMedium
        
          kLong
        """
        __members__: typing.ClassVar[dict[str, TimeOfFlight.RangingMode]]  # value = {'kShort': <RangingMode.kShort: 0>, 'kMedium': <RangingMode.kMedium: 1>, 'kLong': <RangingMode.kLong: 2>}
        kLong: typing.ClassVar[TimeOfFlight.RangingMode]  # value = <RangingMode.kLong: 2>
        kMedium: typing.ClassVar[TimeOfFlight.RangingMode]  # value = <RangingMode.kMedium: 1>
        kShort: typing.ClassVar[TimeOfFlight.RangingMode]  # value = <RangingMode.kShort: 0>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    class Status:
        """
        Members:
        
          kValid
        
          kSigmaHigh
        
          kReturnSignalLow
        
          kReturnPhaseBad
        
          kHardwareFailure
        
          kWrappedTarget
        
          kInternalError
        
          kInvalid
        """
        __members__: typing.ClassVar[dict[str, TimeOfFlight.Status]]  # value = {'kValid': <Status.kValid: 0>, 'kSigmaHigh': <Status.kSigmaHigh: 1>, 'kReturnSignalLow': <Status.kReturnSignalLow: 2>, 'kReturnPhaseBad': <Status.kReturnPhaseBad: 4>, 'kHardwareFailure': <Status.kHardwareFailure: 5>, 'kWrappedTarget': <Status.kWrappedTarget: 7>, 'kInternalError': <Status.kInternalError: 8>, 'kInvalid': <Status.kInvalid: 14>}
        kHardwareFailure: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kHardwareFailure: 5>
        kInternalError: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kInternalError: 8>
        kInvalid: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kInvalid: 14>
        kReturnPhaseBad: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kReturnPhaseBad: 4>
        kReturnSignalLow: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kReturnSignalLow: 2>
        kSigmaHigh: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kSigmaHigh: 1>
        kValid: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kValid: 0>
        kWrappedTarget: typing.ClassVar[TimeOfFlight.Status]  # value = <Status.kWrappedTarget: 7>
        def __eq__(self, other: typing.Any) -> bool:
            ...
        def __getstate__(self) -> int:
            ...
        def __hash__(self) -> int:
            ...
        def __index__(self) -> int:
            ...
        def __init__(self, value: typing.SupportsInt) -> None:
            ...
        def __int__(self) -> int:
            ...
        def __ne__(self, other: typing.Any) -> bool:
            ...
        def __repr__(self) -> str:
            ...
        def __setstate__(self, state: typing.SupportsInt) -> None:
            ...
        def __str__(self) -> str:
            ...
        @property
        def name(self) -> str:
            ...
        @property
        def value(self) -> int:
            ...
    def __init__(self, sensorID: typing.SupportsInt) -> None:
        ...
    def getAmbientLightLevel(self) -> float:
        ...
    def getFirmwareVersion(self) -> int:
        ...
    def getRange(self) -> float:
        ...
    def getRangeSigma(self) -> float:
        ...
    def getSerialNumber(self) -> int:
        ...
    def getStatus(self) -> TimeOfFlight.Status:
        ...
    def identifySensor(self) -> None:
        ...
    def initSendable(self, builder: wpiutil._wpiutil.SendableBuilder) -> None:
        ...
    def isRangeValid(self) -> bool:
        ...
    def setRangeOfInterest(self, topLeftX: typing.SupportsInt, topLeftY: typing.SupportsInt, bottomRightX: typing.SupportsInt, bottomRightY: typing.SupportsInt) -> None:
        ...
    def setRangingMode(self, mode: TimeOfFlight.RangingMode, sampleTime: typing.SupportsFloat) -> None:
        ...
