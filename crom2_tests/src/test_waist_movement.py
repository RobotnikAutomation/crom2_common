#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2015, Robotnik Automation SLL
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Robotnik Automation SSL nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import rospy 

import time, threading, copy, math

from robotnik_msgs.msg import State
from sensor_msgs.msg import JointState

DEFAULT_FREQ = 100.0
MAX_FREQ = 500.0

	
# Class Template of Robotnik component for Pyhton
class RComponent:
	
	def __init__(self, args):
		
		self.node_name = rospy.get_name().replace('/','')
		self.desired_freq = args['desired_freq'] 
		# Checks value of freq
		if self.desired_freq <= 0.0 or self.desired_freq > MAX_FREQ:
			rospy.loginfo('%s::init: Desired freq (%f) is not possible. Setting desired_freq to %f'%(self.node_name,self.desired_freq, DEFAULT_FREQ))
			self.desired_freq = DEFAULT_FREQ
	
	
		self.real_freq = 0.0
		
		# Saves the state of the component
		self.state = State.INIT_STATE
		# Saves the previous state
		self.previous_state = State.INIT_STATE
		# flag to control the initialization of the component
		self.initialized = False
		# flag to control the initialization of ROS stuff
		self.ros_initialized = False
		# flag to control that the control loop is running
		self.running = False
		# Variable used to control the loop frequency
		self.time_sleep = 1.0 / self.desired_freq
		# State msg to publish
		self.msg_state = State()
		# Timer to publish state
		self.publish_state_timer = 1
		
		self._target_joint = 'waist_joint'
		self._target_positions = [0, 1.5, -1.5]
		self._target_velocities = [0.5, 0.5, 0.5]
		self._error_position = 0.01
		self._next_position = 0
		self._last_position = -1
		self._num_of_measurments = 0
		self._total_error = 0.0
		
		self._joint_state_msg = JointState()
		self.t_publish_state = threading.Timer(self.publish_state_timer, self.publishROSstate)
		
			
	def setup(self):
		'''
			Initializes de hand
			@return: True if OK, False otherwise
		'''
		self.initialized = True
		
		return 0
		
		
	def rosSetup(self):
		'''
			Creates and inits ROS components
		'''
		if self.ros_initialized:
			return 0
		
		# Publishers
		self._state_publisher = rospy.Publisher('~state', State, queue_size=10)
		self._command_publisher = rospy.Publisher('/joint_commands', JointState, queue_size=1)
		# Subscribers
		# topic_name, msg type, callback, queue_size
		self.topic_sub = rospy.Subscriber('/joint_states', JointState, self.jointstatesCb, queue_size = 10)
		
		# Service Servers
		# self.service_server = rospy.Service('~service', Empty, self.serviceCb)
		# Service Clients
		# self.service_client = rospy.ServiceProxy('service_name', ServiceMsg)
		# ret = self.service_client.call(ServiceMsg)
		
		self.ros_initialized = True
		
		self.publishROSstate()
		
		return 0
		
		
	def shutdown(self):
		'''
			Shutdowns device
			@return: 0 if it's performed successfully, -1 if there's any problem or the component is running
		'''
		if self.running or not self.initialized:
			return -1
		rospy.loginfo('%s::shutdown'%self.node_name)
		
		# Cancels current timers
		self.t_publish_state.cancel()
		
		self._state_publisher.unregister()
		
		self.initialized = False
		
		return 0
	
	
	def rosShutdown(self):
		'''
			Shutdows all ROS components
			@return: 0 if it's performed successfully, -1 if there's any problem or the component is running
		'''
		if self.running or not self.ros_initialized:
			return -1
		
		# Performs ROS topics & services shutdown
		self._state_publisher.unregister()
		
		self.ros_initialized = False
		
		return 0
			
	
	def stop(self):
		'''
			Creates and inits ROS components
		'''
		self.running = False
		
		return 0
	
	
	def start(self):
		'''
			Runs ROS configuration and the main control loop
			@return: 0 if OK
		'''
		self.rosSetup()
		
		if self.running:
			return 0
			
		self.running = True
		
		self.controlLoop()
		
		return 0
	
	
	def controlLoop(self):
		'''
			Main loop of the component
			Manages actions by state
		'''
		
		while self.running and not rospy.is_shutdown():
			t1 = time.time()
			
			if self.state == State.INIT_STATE:
				self.initState()
				
			elif self.state == State.STANDBY_STATE:
				self.standbyState()
				
			elif self.state == State.READY_STATE:
				self.readyState()
				
			elif self.state == State.EMERGENCY_STATE:
				self.emergencyState()
				
			elif self.state == State.FAILURE_STATE:
				self.failureState()
				
			elif self.state == State.SHUTDOWN_STATE:
				self.shutdownState()
				
			self.allState()
			
			t2 = time.time()
			tdiff = (t2 - t1)
			
			
			t_sleep = self.time_sleep - tdiff
			
			if t_sleep > 0.0:
				try:
					rospy.sleep(t_sleep)
				except rospy.exceptions.ROSInterruptException:
					rospy.loginfo('%s::controlLoop: ROS interrupt exception'%self.node_name)
					self.running = False
			
			t3= time.time()
			self.real_freq = 1.0/(t3 - t1)
		
		self.running = False
		# Performs component shutdown
		self.shutdownState()
		# Performs ROS shutdown
		self.rosShutdown()
		rospy.loginfo('%s::controlLoop: exit control loop'%self.node_name)
		
		return 0
		
		
	def rosPublish(self):
		'''
			Publish topics at standard frequency
		'''
					
		return 0
		
	
	def initState(self):
		'''
			Actions performed in init state
		'''
		
		if not self.initialized:
			self.setup()
			
		else: 		
			self.switchToState(State.STANDBY_STATE)
		
		
		return
	
	
	def standbyState(self):
		'''
			Actions performed in standby state
		'''
		if self._last_position >= 0:
			if len(self._joint_state_msg.position)> 0:
				self._num_of_measurments += 1
				
				current_position = self._joint_state_msg.position[0]
				target_position = self._target_positions[self._last_position]
				error = target_position - current_position
				self._total_error+= abs(error)
				rospy.logwarn('standbyState: current = %.3lf, target = %.3lf, error = %lf, avg error = %lf', math.degrees(current_position), math.degrees(target_position), math.degrees(error), math.degrees(self._total_error/self._num_of_measurments))
			
		self.switchToState(State.READY_STATE)
		
		return
	
	
	def readyState(self):
		'''
			Actions performed in ready state
		'''
		if len(self._joint_state_msg.position)> 0:
			
			current_position = self._joint_state_msg.position[0]
			
			if abs(current_position - self._target_positions[self._next_position])<= self._error_position:
				self._last_position = copy.deepcopy(self._next_position)
				self._next_position = (self._next_position + 1)%len(self._target_positions)
				
				self.switchToState(State.STANDBY_STATE)
			else:
				msg = JointState()
				msg.header.stamp = rospy.Time.now()
				msg.name = [self._target_joint]
				msg.position = [self._target_positions[self._next_position]]
				msg.velocity = [self._target_velocities[self._next_position]]
				msg.effort = []
				self._command_publisher.publish(msg)
		
		return
		
	
	def shutdownState(self):
		'''
			Actions performed in shutdown state 
		'''
		if self.shutdown() == 0:
			self.switchToState(State.INIT_STATE)
		
		return
	
	
	def emergencyState(self):
		'''
			Actions performed in emergency state
		'''
		
		return
	
	
	def failureState(self):
		'''
			Actions performed in failure state
		'''
		
			
		return
	
	
	def switchToState(self, new_state):
		'''
			Performs the change of state
		'''
		if self.state != new_state:
			self.previous_state = self.state
			
			if new_state == State.READY_STATE:
				msg = JointState()
				msg.header.stamp = rospy.Time.now()
				msg.name = [self._target_joint]
				msg.position = [self._target_positions[self._next_position]]
				msg.velocity = [self._target_velocities[self._next_position]]
				msg.effort = []
				print msg
				self._command_publisher.publish(msg)
				rospy.loginfo('%s::switchToState: publish'%(self.node_name))
			elif new_state == State.STANDBY_STATE:
				rospy.sleep(5.0)
				
			self.state = new_state
			rospy.loginfo('%s::switchToState: %s'%(self.node_name, self.stateToString(self.state)))
			
			
		
		return
	
		
	def allState(self):
		'''
			Actions performed in all states
		'''
		self.rosPublish()
		
		return
	
	
	def stateToString(self, state):
		'''
			@param state: state to set
			@type state: State
			@returns the equivalent string of the state
		'''
		if state == State.INIT_STATE:
			return 'INIT_STATE'
				
		elif state == State.STANDBY_STATE:
			return 'STANDBY_STATE'
			
		elif state == State.READY_STATE:
			return 'READY_STATE'
			
		elif state == State.EMERGENCY_STATE:
			return 'EMERGENCY_STATE'
			
		elif state == State.FAILURE_STATE:
			return 'FAILURE_STATE'
			
		elif state == State.SHUTDOWN_STATE:
			return 'SHUTDOWN_STATE'
		else:
			return 'UNKNOWN_STATE'
	
		
	def publishROSstate(self):
		'''
			Publish the State of the component at the desired frequency
		'''
		self.msg_state.state = self.state
		self.msg_state.state_description = self.stateToString(self.state)
		self.msg_state.desired_freq = self.desired_freq
		self.msg_state.real_freq = self.real_freq
		self._state_publisher.publish(self.msg_state)
		
		self.t_publish_state = threading.Timer(self.publish_state_timer, self.publishROSstate)
		self.t_publish_state.start()
	
	
	def jointstatesCb(self, msg):
		'''

		'''
		# DEMO
		self._joint_state_msg = msg
		#rospy.loginfo('RComponent:jointstatesCb')
		
		

	"""
	def serviceCb(self, req):
		'''
			ROS service server
			@param req: Required action
			@type req: std_srv/Empty
		'''
		# DEMO
		rospy.loginfo('RComponent:serviceCb')	
	"""	
		
def main():

	rospy.init_node("crom_test_torso")
	
	
	_name = rospy.get_name().replace('/','')
	
	arg_defaults = {
	  'topic_state': 'state',
	  'desired_freq': DEFAULT_FREQ,
	}
	
	args = {}
	
	for name in arg_defaults:
		try:
			if rospy.search_param(name): 
				args[name] = rospy.get_param('~%s'%(name)) # Adding the name of the node, because the para has the namespace of the node
			else:
				args[name] = arg_defaults[name]
			#print name
		except rospy.ROSException, e:
			rospy.logerr('%s: %s'%(e, _name))
			
	
	rc_node = RComponent(args)
	
	rospy.loginfo('%s: starting'%(_name))

	rc_node.start()


if __name__ == "__main__":
	main()
