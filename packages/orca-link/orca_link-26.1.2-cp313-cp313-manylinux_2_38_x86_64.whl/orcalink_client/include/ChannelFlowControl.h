#ifndef __CHANNEL_FLOW_CONTROL_H__
#define __CHANNEL_FLOW_CONTROL_H__

#include <cstdint>

namespace OrcaLink {

/**
 * @brief Channel-level flow control for bidirectional communication
 * 
 * Tracks send/receive counts to detect speed mismatches between coupled simulations.
 * Supports single-direction and bidirectional channels.
 */
class ChannelFlowControl {
public:
    /**
     * @brief Channel statistics
     */
    struct Stats {
        uint64_t sendCount = 0;          ///< Number of messages sent
        uint64_t recvCount = 0;          ///< Number of messages received
        int64_t sendAhead = 0;           ///< How many frames ahead (sendCount - recvCount)
        bool isPaused = false;           ///< Whether flow control is active
        uint64_t totalPauses = 0;        ///< Total number of pauses triggered
        uint64_t lastLogFrame = 0;       ///< Last frame when status was logged
    };
    
    /**
     * @brief Constructor
     * @param channelId Channel identifier
     * @param isPublisher Whether this channel publishes data
     * @param isSubscriber Whether this channel subscribes to data
     */
    ChannelFlowControl(uint32_t channelId, bool isPublisher, bool isSubscriber);
    
    /**
     * @brief Record a sent message
     */
    void RecordSend();
    
    /**
     * @brief Record received messages
     * @param count Number of messages received (default: 1)
     */
    void RecordRecv(uint32_t count = 1);
    
    /**
     * @brief Check if flow control should pause
     * @param maxAhead Maximum allowed frames ahead
     * @return true if sendAhead > maxAhead and channel is bidirectional
     */
    bool ShouldPause(uint32_t maxAhead) const;
    
    /**
     * @brief Check if flow control can resume
     * @param minAhead Minimum frames to consider as synchronized
     * @return true if sendAhead <= minAhead
     */
    bool CanResume(uint32_t minAhead) const;
    
    /**
     * @brief Check if channel is bidirectional
     * @return true if both publishing and subscribing
     */
    bool IsBidirectional() const { return m_isPublisher && m_isSubscriber; }
    
    /**
     * @brief Set paused state
     * @param paused New pause state
     */
    void SetPaused(bool paused);
    
    /**
     * @brief Set remote ACK sequence number (for bounded async flow control)
     * @param sequence Remote client's acknowledged sequence
     */
    void SetRemoteAckedSequence(uint64_t sequence) { m_remoteAckedSequence = sequence; }
    
    /**
     * @brief Get remote ACK sequence number
     */
    uint64_t GetRemoteAckedSequence() const { return m_remoteAckedSequence; }
    
    /**
     * @brief Set paused ACK baseline (for bounded async recovery)
     * @param baseline ACK sequence when pause occurred
     */
    void SetPausedAckedBaseline(uint64_t baseline) { m_pausedAckedBaseline = baseline; }
    
    /**
     * @brief Get paused ACK baseline
     */
    uint64_t GetPausedAckedBaseline() const { return m_pausedAckedBaseline; }
    
    /**
     * @brief Get current statistics
     */
    const Stats& GetStats() const { return m_stats; }

private:
    /**
     * @brief Update the sendAhead value
     */
    void UpdateSendAhead();
    
    uint32_t m_channelId;
    bool m_isPublisher;
    bool m_isSubscriber;
    Stats m_stats;
    
    // ACK and bounded async flow control (NEW)
    uint64_t m_remoteAckedSequence = 0;  ///< Remote client's ACK sequence
    uint64_t m_pausedAckedBaseline = 0;  ///< ACK baseline when pause occurred
};

} // namespace OrcaLink

#endif // __CHANNEL_FLOW_CONTROL_H__

