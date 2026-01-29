"""
Real-Time Behavioral Anomaly Alerts

Instant alerts when users behave unusually, with automatic root cause analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import uuid

from ..anomaly_detection import AnomalyDetector, AnomalyDetectionConfig
from ..types import Anomaly


class Alert(BaseModel):
    """Represents a real-time anomaly alert."""

    alert_id: str = Field(..., description="Unique alert identifier")
    anomaly_id: str = Field(..., description="Associated anomaly ID")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$")
    message: str = Field(..., description="Alert message")
    root_cause: Optional[str] = Field(None, description="Root cause analysis")
    suggestions: List[str] = Field(default_factory=list, description="Fix suggestions")
    timestamp: datetime = Field(default_factory=datetime.now)
    event: Dict[str, Any] = Field(..., description="Anomalous event")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BehavioralAnomalyAlerts:
    """
    Real-time behavioral anomaly detection and alerting system.

    Detects unusual behavioral patterns instantly and provides
    automatic root cause analysis with suggested fixes.
    """

    def __init__(
        self,
        config: Optional[AnomalyDetectionConfig] = None,
        enable_root_cause: bool = True,
    ):
        """
        Initialize behavioral anomaly alerts.

        Args:
            config: Anomaly detection configuration
            enable_root_cause: Enable root cause analysis
        """
        if config is None:
            config = AnomalyDetectionConfig(real_time_enabled=True)

        self.detector = AnomalyDetector(config)
        self.enable_root_cause = enable_root_cause
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[callable] = []

    def process_event(self, event: Dict[str, Any]) -> Optional[Alert]:
        """
        Process event and generate alert if anomaly detected.

        Args:
            event: Event to process

        Returns:
            Alert if anomaly detected, None otherwise
        """
        # Detect anomaly in real-time
        is_anomaly = self.detector.detect_realtime(event)

        if not is_anomaly:
            return None

        # Get anomaly details
        anomalies = self.detector.detect([event])
        if not anomalies:
            return None

        anomaly = anomalies[0]

        # Generate alert
        alert = self._create_alert(anomaly, event)

        # Store alert
        self.alert_history.append(alert)

        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass  # Ignore callback errors

        return alert

    def _create_alert(self, anomaly: Anomaly, event: Dict[str, Any]) -> Alert:
        """
        Create alert from anomaly.

        Args:
            anomaly: Detected anomaly
            event: Anomalous event

        Returns:
            Alert object
        """
        # Generate alert message
        message = self._generate_alert_message(anomaly)

        # Root cause analysis
        root_cause = None
        suggestions = []
        if self.enable_root_cause:
            root_cause = self._analyze_root_cause(anomaly, event)
            suggestions = self._generate_suggestions(anomaly, root_cause)

        return Alert(
            alert_id=f"alert_{uuid.uuid4().hex[:8]}",
            anomaly_id=anomaly.anomaly_id,
            severity=anomaly.severity,
            message=message,
            root_cause=root_cause,
            suggestions=suggestions,
            event=event,
            metadata={"anomaly_score": anomaly.anomaly_score},
        )

    def _generate_alert_message(self, anomaly: Anomaly) -> str:
        """
        Generate alert message.

        Args:
            anomaly: Detected anomaly

        Returns:
            Alert message
        """
        event_type = anomaly.event.get("type", "unknown")
        severity = anomaly.severity.upper()

        return (
            f"[{severity}] Anomalous {event_type} event detected. "
            f"Score: {anomaly.anomaly_score:.2f}"
        )

    def _analyze_root_cause(
        self, anomaly: Anomaly, event: Dict[str, Any]
    ) -> Optional[str]:
        """
        Analyze root cause of anomaly.

        Args:
            anomaly: Detected anomaly
            event: Anomalous event

        Returns:
            Root cause analysis
        """
        # Simple heuristic-based root cause analysis
        # In production, this would use LLM or more sophisticated analysis

        event_type = event.get("type", "")
        duration = event.get("duration", 0)
        error_count = sum(1 for k in event.keys() if "error" in k.lower())

        if error_count > 0:
            return "High error rate detected in event metadata"
        elif duration > 10000:  # >10 seconds
            return "Unusually long event duration suggests performance issues"
        elif event_type == "error":
            return "Error event detected - possible system or user issue"
        elif anomaly.anomaly_score > 0.9:
            return "Extremely unusual behavioral pattern detected"
        else:
            return "Behavioral pattern deviates significantly from normal"

    def _generate_suggestions(
        self, anomaly: Anomaly, root_cause: Optional[str]
    ) -> List[str]:
        """
        Generate fix suggestions.

        Args:
            anomaly: Detected anomaly
            root_cause: Root cause analysis

        Returns:
            List of suggestions
        """
        suggestions = []

        if root_cause and "error" in root_cause.lower():
            suggestions.append("Check system logs for error details")
            suggestions.append("Verify user permissions and access")
            suggestions.append("Review recent system changes")

        if root_cause and "performance" in root_cause.lower():
            suggestions.append("Check server response times")
            suggestions.append("Review database query performance")
            suggestions.append("Monitor resource usage")

        if anomaly.severity in ["high", "critical"]:
            suggestions.append("Immediate investigation recommended")
            suggestions.append("Consider user notification or intervention")

        if not suggestions:
            suggestions.append("Monitor for similar patterns")
            suggestions.append("Review user session context")

        return suggestions

    def send_alert(self, alert: Alert) -> None:
        """
        Send alert to configured channels.

        Args:
            alert: Alert to send
        """
        # In production, this would send to email, Slack, webhook, etc.
        # For now, just store in history
        self.alert_history.append(alert)

    def get_alert_history(
        self, time_period: str = "24hours", severity: Optional[str] = None
    ) -> List[Alert]:
        """
        Get alert history.

        Args:
            time_period: Time period to retrieve (e.g., "24hours", "7days")
            severity: Filter by severity level

        Returns:
            List of alerts
        """
        # Parse time period
        if time_period.endswith("hours"):
            hours = int(time_period[:-5])
            cutoff = datetime.now() - timedelta(hours=hours)
        elif time_period.endswith("days"):
            days = int(time_period[:-4])
            cutoff = datetime.now() - timedelta(days=days)
        else:
            cutoff = datetime.now() - timedelta(hours=24)

        # Filter alerts
        alerts = [
            a
            for a in self.alert_history
            if a.timestamp >= cutoff
            and (severity is None or a.severity == severity)
        ]

        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def register_callback(self, callback: callable) -> None:
        """
        Register callback for alerts.

        Args:
            callback: Function to call when alert is generated
        """
        self.alert_callbacks.append(callback)

    def clear_history(self) -> None:
        """Clear alert history."""
        self.alert_history.clear()
