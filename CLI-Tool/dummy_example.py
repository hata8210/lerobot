#导入依赖
import ref_tool
#初始化机械臂
my_drive = ref_tool.find_any() #找到dummy设备
my_drive.robot.set_enable(1)  #电机使能
my_drive.robot.set_rgb_mode(4) #使能后把指示灯设置为4绿灯，未使能则是0跑马灯
my_drive.robot.homing() #设置为初始位姿

#程序angle与实际的偏差，joint角度实际数值 = joint角度程序值 - joint角度偏差值
joint1bia = 0
joint2bia = 77
joint3bia = -185
joint4bia = 0
joint5bia = 0
joint6bia = 0
#获取当前每个joint角度的程序值，并转化为joint角度的实际值
joint1angle = my_drive.robot.joint_1.angle - joint1bia
joint2angle = my_drive.robot.joint_2.angle - joint2bia
joint3angle = my_drive.robot.joint_3.angle - joint3bia
joint4angle = my_drive.robot.joint_4.angle - joint4bia
joint5angle = my_drive.robot.joint_5.angle - joint5bia
joint6angle = my_drive.robot.joint_6.angle - joint6bia
#本次需要增量动作角度，joint2向前加45度
joint1move = 0
joint2move = 45
joint3move = 0
joint4move = 0
joint5move = 0
joint6move = 0
#机械臂行动
joint1angle = joint1angle + joint1move
joint2angle = joint2angle + joint2move
joint3angle = joint3angle + joint3move
joint4angle = joint4angle + joint4move
joint5angle = joint5angle + joint5move
joint6angle = joint6angle + joint6move
my_drive.robot.move_j(joint1angle,joint2angle,joint3angle,joint4angle,joint5angle,joint6angle) 


