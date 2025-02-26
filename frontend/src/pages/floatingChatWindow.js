import React, {Component} from 'react'
import {Launcher} from 'react-chat-window'
import VideoPlayer from "./getVideoFromBackend";
 
class FloatingWindow extends Component {
 
  constructor() {
    super();
    this.state = {
      messageList: []
    };
  }
 
  _onMessageWasSent = (message) => {
    this.setState({
      messageList: [...this.state.messageList, message]
    })
  }
 
  _sendMessage = (text) => {
    if (text.length > 0) {
      this.setState({
        messageList: [...this.state.messageList, {
          author: 'them',
          type: 'text',
          data: { text }
        }]
      })
    }
  }
 
  render() {
    const agentProfile = {
        teamName: 'Real-time Commentary',
        imageUrl: '/chatgpt.png'
    };

    if (this.props.forwardedSendMessage) {
        this.props.forwardedSendMessage(this._sendMessage);
    }

    return (
    <div>
        <Launcher
            agentProfile={agentProfile}
            onMessageWasSent={this._onMessageWasSent.bind(this)}
            messageList={this.state.messageList}
            showEmoji
        />
    </div>)
  }
}

export default FloatingWindow;