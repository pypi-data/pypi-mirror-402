###### 虚拟控制器---API 示例
###### 
###### Date: 2024-5-16
###### Modify : 2024-5-17
####
# add modbus TCP Server -- 2024-5-17
# add modbus TCP Client 读写寄存器地址 -- 2024-5-20
####

import  os, socket,  inspect, threading, struct
from struct import pack, unpack
import json, time, logging, re

import modbus_tk.modbus_tcp as modbus_tcp
from modbus_tk.modbus_rtu import RtuServer
import modbus_tk.defines as cst

FolderPath = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
robot_logger=logging.getLogger("Controler-Driver")
robot_logger.setLevel(logging.DEBUG)

class Virtual_WlkataMirobot():

    def __init__(self,server_IP='', server_port=None):
        self.server_IP = server_IP  
        self.server_port = server_port
        self.invalid_IP_Port_Connect()

        self.modbus_host = "0.0.0.0"
        self.modbus_port = 502

        self.robot_type = 1
        self.global_state = [1,1,1]
        self.IO = [0,0,0,0,0,0,0,0]
        self.default_speed = 1000
        ####
        self.status_state = None
        self.status_state2 = None

        ### 第七轴/滑轨
        self.angles_7 = 0
        self.angles_7_com2 = 0

        #### modbus 寄存器初始化
        self.modbus_tcp_init()
        self.master = modbus_tcp.TcpMaster(host="127.0.0.1", port=502)

        ### 接收数据线程
        self.recv_thread_flag = True
        receive_thread = threading.Thread(target = self.receive_data_from_server) 
        receive_thread.start() 

    def modbus_tcp_init(self,):
        self.modus_server = modbus_tcp.TcpServer(port= self.modbus_port , address=self.modbus_host )
        self.modus_server.start()
        self.register_init()

    def register_init(self):
        #### 服务器上创建1号从机
        self.slave = self.modus_server.add_slave(1)
        #### 创建400个保持寄存器
        self.slave.add_block('robot_Virtual', cst.HOLDING_REGISTERS, 0, 400)

    
    ### 机器人状态寄存器地址0位
    def modbus_Set_robot_Status(self, status):
        try:
            st = []
            if status is not None:
                match status:
                    case "Idle":
                        st = st + [1]
                    case "Alarm":
                        st = st + [2]
                    case "Home":
                        st = st + [3]
                    case "Run":
                        st = st + [4]
                    case _:
                        st = st + [0]
                self.slave.set_values("robot_Virtual", 0, st)
        
        except Exception as e:
            pass
            robot_logger.error(f"modbus_Set_robot_Status error: {e}")
    ### 轴角信号寄存器地址1开始
    def modbus_Set_robot_Angles(self, angle):
        try:
            if angle is not None:
                P = []
                for i in range(0,6):
                    P.append(self.float2int16s(angle[i]))
                    
                extracted_values = [value for sublist in P for value in sublist]
                for i, value in enumerate(extracted_values, start=1):
                    self.slave.set_values("robot_Virtual", i, value)  

        except Exception as e:
            robot_logger.error(f"modbus_Set_robot_Angles error: {e}")
    ### DI信号寄存器地址73开始
    def modbus_Set_Input_Status(self, input_status):
        try:
            extracted_values = [value for sublist in input_status for value in sublist]
            cleaned_values = [int(value) for value in extracted_values if value.isdigit()]
            for i, value in enumerate(cleaned_values, start=73):
                self.slave.set_values("robot_Virtual", i, value) 
        
        except Exception as e:
            robot_logger.error(f"modbus_Set_Input_Status error: {e}")
    ### DO信号寄存器地址94开始
    def modbus_Set_Output_Status(self, output_status):
        try:
            extracted_values = output_status
            for i, value in enumerate(extracted_values, start=94):
                self.slave.set_values("robot_Virtual", i, value) 
        
        except Exception as e:
            robot_logger.error(f"modbus_Set_Output_Status error: {e}")
    ### 读保持寄存器地址
    def get_modbusValues(self, address, count):
        try:
            values =  self.master.execute(1, cst.READ_HOLDING_REGISTERS, address, 1)
            return values
        except Exception as e:
            robot_logger.error(f"get_modbusValues error: {e}")
    ### 写单个保持寄存器地址
    def set_Single_modbusValues(self, address, values):
        try:
            self.master.execute(1, cst.WRITE_SINGLE_REGISTER, starting_address=address, output_value=values)
        except Exception as e:
            robot_logger.error(f"set_modbusValues error: {e}")
    ### 写多个保持寄存器地址
    def set_Multi_modbusValues(self, address, values):
        try:
            self.master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, starting_address=address, quantity_of_x=len(values), output_value=values)
        except Exception as e:
            robot_logger.error(f"set_modbusValues error: {e}")
    
    
    def float2int16s(self, f):
        ## 将浮点数打包成32位二进制数据
        b = struct.pack('f', f)
        ## 将32位二进制数据拆分成两个16位二进制数据
        i1, i2 = struct.unpack('HH', b)
        return i2, i1

    ### 作为client 连接服务端--Start
    def invalid_IP_Port_Connect(self,):
        self.flag = False
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #### 更改IP/PORT连接服务端 
        if self.server_IP == '':
            print(f"Please check ip is NULL")
            return
        
        #### 端口号 可以自行更改
        if self.server_port == '':  
            print(f"Please check port is NULL")
            return

        if len(self.server_IP) != 0 and not self.server_port is None:
            try:
                ip_pattern = r'^((25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)\.){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|\d)$'  
                if not re.match(ip_pattern, self.server_IP):  
                    return False, 'Invalid IP address'  
                
                self.client_socket.connect((self.server_IP, self.server_port))
                self.flag = True
                print(f"Connected to {self.server_IP}:{self.server_port}")
            
            except ValueError:
                print(f"Please input the right ip/port")
                return

    def receive_data_from_server(self,):
        while True:
                try:
                    ### 处理接收到的数据
                    msg = self.client_socket.recv(1024).decode("utf-8")
                    # print(f"接收: {msg}")

                    # 正则表达式来匹配可能的JSON对象（这里简化了匹配规则，可能需要根据实际情况调整）  
                    # pattern = r'"com1State":"(\w+)"'
                    pattern = r'"com1State":"(\w*)","com2State":"(\w*)"'
                   
                    match = re.search(pattern, msg)
                    if match:
                        self.status_state = match.group(1)
                        self.status_state2 = match.group(2)
                
                    else:
                        self.status_state = None
                        self.status_state2 = None
                        print("No match found state")
                    time.sleep(0.01)

                    pattern_io = r'"IO":\[([^\]]+)\]'
                    match_io = re.search(pattern_io, msg)
                    input = match_io.group(1)
                    self.modbus_Set_Input_Status(input)
                    self.modbus_Set_robot_Status(self.status_state)

                except Exception as e:
                    print(e)

    def disConnected(self):
        self.client_socket.close()

    ### 虚拟控制器测试代码--单元
    # 定义通讯协议格式  
    def build_packet(self,data_size, packet_type, message_body):  
        # 构建报头  
        header = json.dumps({  
            "data_size": data_size,  
            "type": packet_type  
        }).encode('utf-8')
        
        # 计算报头长度（4位bit，即半个字节，需要转换为字节长度）  
        header_length = len(header)
        # print(header_length)
        
        # 构建帧头
        # frame_header = struct.pack('>H', header_length)
        frame_header = header_length.to_bytes(4, 'little')
        # print(frame_header)
        
        # 完整的数据包  
        packet = frame_header + header + message_body.encode('utf-8')
        return packet 

    # 定义消息体  --- 发送至虚拟控制器
    def create_message_body(self,robot_type, state, com1, com2, rs485, com1Float, com2Float,io):  
        message_body = {  
            "robot_type": robot_type,  
            "state": state,  
            "com1": com1,  
            "com2": com2,  
            "RS485": rs485, 
            "com1Float": com1Float,
            "com2Float": com2Float,
            "IO": io  
        }  
        return json.dumps(message_body)  

    def validJog_Cartians_Speed(self, text):
        try:
            value = float(text)
            if value < -100 or value > 160:
                print ("Value out of range")
        except ValueError:
            print()

    def send_msg(self, com1_data=None, com2_data = None, wait_idle=False):
        robot_type = self.robot_type
        state = self.global_state
        com1 = com1_data
        com2 = com2_data
        rs485 = ""
        com1Float = self.angles_7 
        com2Float = self.angles_7_com2
        io = self.IO
        
        ### 消息体
        message_body = self.create_message_body(robot_type, state, com1, com2, rs485, com1Float, com2Float, io)
        ### 消息体长度
        data_size = len(message_body)
        ### 控制器类型：虚拟控制器
        packet_type = "virtual" 
        ### 构建数据包 
        packet = self.build_packet(data_size, packet_type, message_body)
        self.client_socket.sendall(packet)
        time.sleep(0.5)

        if wait_idle is None:
            wait_idle = False
        
        if wait_idle:
                self.wait_until_idle(com1_data=com1_data,com2_data = com2_data)

    def wait_until_idle(self, com1_data=None,com2_data = None, refresh_rate = 0.1):
        if com1_data is not None:
            while self.status_state != "Idle":
                time.sleep(refresh_rate)
                continue
        elif com2_data is not None:
            while self.status_state2 != "Idle":
                time.sleep(refresh_rate)
                continue
        else:
            while self.status_state != "Idle" or self.status_state is None:
                time.sleep(refresh_rate)
                continue

    ### G代码指令转换
    ### API函数
    ### IO输出设置
    def set_7axis(self, com1_7axis = None, com2_7axis = None):
            self.angles_7 = com1_7axis
            self.angles_7_com2 = com2_7axis
            return self.send_msg(wait_idle=True)

    def set_Output(self, output_id, value):
            self.IO[output_id] = value
            IO_temp = self.IO
            self.modbus_Set_Output_Status(IO_temp)
            return self.send_msg(wait_idle=True)
    
    def get_Input(self, input_id):
        try:
            msg = self.client_socket.recv(1024).decode("utf-8")
            pattern = r'"IO":\[([^\]]+)\]'
            match = re.search(pattern, msg)
            input = match.group(1)
            input_list = [int(item) for item in input.split(',')]
            input_value = input_list[input_id]
            if input_value == 1:
                return True
            elif input_value == 0:
                return False
        except Exception as e:
            print(e)

    ### 机器人操作
    def home(self, has_slider=False,com1 = False, com2 = False):
        '''机械臂Homing'''
        if com1:
            if has_slider:
                self.home_7axis(com1 = com1)
                return True
            else:
                self.home_6axis(com1 = com1)
                return True
        elif com2:
            if has_slider:
                return self.home_7axis(com2 = com2)
            else:
                self.home_6axis(com2 = com2)
                return True     

    def home_1axis(self, axis_id):
        '''单轴Homing'''
        if not isinstance(axis_id, int) or not (axis_id >= 1 and axis_id <= 7):
            return False
        msg = f'$h{axis_id}'
        return self.send_msg(msg, wait_idle=True)

    def home_6axis(self,com1 = False, com2 = False):
        '''六轴Homing'''
        msg = f'$h'
        if com1:
            self.send_msg(com1_data=msg, wait_idle=True)
        elif com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        return True

    def home_6axis_in_turn(self):
        '''六轴Homing, 各关节依次Homing'''
        msg = f'$hh'
        return self.send_msg(msg, wait_idle=True)
    
    def stop(self):
        '''6轴暂停'''
        msg = f'!'
        self.send_msg(msg)
        time.sleep(0.5)
        msg = f'%'
        return self.send_msg(msg)

    def home_7axis(self, com1= False, com2 = False):
        '''七轴Homing(本体 + 滑台)'''
        msg = f'$h0'
        if com1:
            self.send_msg(com1_data=msg, wait_idle=True)
        elif com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        return True
        
    def unlock_all_axis(self):
        '''解锁各轴锁定状态'''
        msg = 'M50'
        return self.send_msg(msg, wait_idle=True)
        
    def go_to_zero(self,com1 = False, com2 = False):
        '''回零-运动到名义上的各轴零点'''
        msg = 'M21 G90 G00 X0 Y0 Z0 A0 B0 C0 F2000'
        if com1:
            self.send_msg(com1_data=msg, wait_idle=True)
        elif com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        return True

    def set_speed(self, speed):
        '''设置转速'''
        # 转换为整数
        speed = int(speed)
        # 检查数值范围是否合法
        if speed <= 0 or speed > 6000:
            robot_logger.error(f"Illegal movement speed {speed}")
            return False
        # 发送指令
        msg = f'F{speed}'
        return self.send_msg(msg )

    def set_hard_limit(self, enable):
        '''
        开启硬件限位
        '''
        msg = f'$21={int(enable)}'
        return self.send_msg(msg)

    def set_soft_limit(self, enable):
        '''开启软限位
        注: 请谨慎使用
        '''
        msg = f'$20={int(enable)}'
        return self.send_msg(msg)

    def format_float_value(self, value):
        if value is None:
            return value
        if isinstance(value, float):
            # 精确到小数点后两位数
            return round(value , 2)
        else:
            return value

    def generate_args_string(self, instruction, pairings):
        '''生成参数字符'''
        args = [f'{arg_key}{self.format_float_value(value)}' for arg_key, value in pairings.items() if value is not None]

        return ' '.join([instruction] + args)
        
    def move(self, P, speed = None ,coordinate= 0, is_relative=0,mode =0, wait_ok=None):

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        instruction = 'M20 G90 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
        m1 = "M20"             # 世界坐标系
        pairings = {'X': P[0], 'Y': P[1], 'Z': P[2], 'A': P[3], 'B': P[4], 'C': P[5], 'F': speed}
        if coordinate ==0:
            m1 = "M21"      # 轴角坐标系
        m2 = "G90"
        if is_relative:
            m2 = 'G91'       
        m3 ="G00"
        if mode == 1:
            m3 = "G01"

        instruction = f"{m1} {m2} {m3} "
        
        msg = self.generate_args_string(instruction, pairings)
        return msg

    def set_joint_angle(self, joint_angles=None, com1_P=None, com2_P = None,speed=None, is_relative=False, is_com2 = False, ):
        '''
        设置机械臂关节的角度
        joint_angles 目标关节角度字典, key是关节的ID号, value是角度(单位°)
            举例: {1:45.0, 2:-30.0}
        '''
        if joint_angles is not None:
            for joint_i in range(1, 8):
                # 补齐缺失的角度
                if joint_i not in joint_angles:
                    joint_angles[joint_i] = None
        elif com1_P is not None:
            joint_angles = {1:com1_P[0],2:com1_P[1],3:com1_P[2],4:com1_P[3],5:com1_P[4],6:com1_P[5]}
            time.sleep(0.01)
            self.modbus_Set_robot_Angles(com1_P)
            is_com2 = False
        elif com2_P is not None:
            joint_angles = {1:com2_P[0],2:com2_P[1],3:com2_P[2],4:com2_P[3],5:com2_P[4],6:com2_P[5]}
            is_com2 = True
        else :
            for joint_i in range(1, 7):
                joint_angles[joint_i] = None

        return self.go_to_axis(x=joint_angles[1], y=joint_angles[2], z=joint_angles[3], a=joint_angles[4], \
            b=joint_angles[5], c=joint_angles[6], is_relative=is_relative, speed=speed, is_com2 = is_com2,)

    def go_to_axis(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, is_com2 = False, ):
        '''设置关节角度/位置'''
        instruction = 'M21 G90'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
        if is_relative:
            instruction = 'M21 G91'
        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self.generate_args_string(instruction, pairings)
        if is_com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        else:
            self.send_msg(com1_data=msg, wait_idle=True)

        return True

    def set_tool_pose(self, x=None, y=None, z=None, roll=None, pitch=None, yaw=None, com1_P = None, com2_P = None,mode='p2p', speed=None, is_relative=False, is_com2 = False):
        '''设置工具位姿'''

        if com1_P is not None:
            x = com1_P[6]
            y = com1_P[7]
            z = com1_P[8]
            roll = com1_P[9]
            pitch = com1_P[10]
            yaw = com1_P[11]
            is_com2 = False

            
        if com2_P is not None:
            x= com2_P[6]
            y= com2_P[7]
            z= com2_P[8]
            roll= com2_P[9]
            pitch= com2_P[10]
            yaw= com2_P[11]
            is_com2 = True

        if mode == "p2p":
            # 点控模式 Point To Point
            self.p2p_interpolation(x=x, y=y, z=z, a=roll, b=pitch, c=yaw, speed=speed, is_relative=is_relative, is_com2 = is_com2,)
        elif mode == "linear":
            # 直线插补 Linera Interpolation
            self.linear_interpolation(x=x, y=y, z=z, a=roll, b=pitch, c=yaw, speed=speed,is_relative=is_relative, is_com2 = is_com2,)
        else:
            # 默认是点到点
            self.p2p_interpolation(x=x, y=y, z=z, a=roll, b=pitch, c=yaw, speed=speed, is_com2 = is_com2, wait_idle=wait_idle)

    def p2p_interpolation(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, is_com2 = False):
        '''点到点插补'''
        instruction = 'M20 G90 G0'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
        if is_relative:
            instruction = 'M20 G91 G0'

        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self.generate_args_string(instruction, pairings)
        if is_com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        else:
            self.send_msg(com1_data=msg, wait_idle=True)
        return True
    
    def linear_interpolation(self,P1,speed=None, is_relative=False, is_com2 = False, wait_idle=None):
        self.linear_interpolation_o( x=P1[6], y=P1[7], z=P1[8], a=P1[9], b=P1[10], c=P1[11],
                            speed=speed,is_relative=is_relative,is_com2 = is_com2)
    
    def linear_interpolation_o(self, x=None, y=None, z=None, a=None, b=None, c=None, speed=None, is_relative=False, is_com2 = False):
        '''直线插补'''
        instruction = 'M20 G90 G1'  # X{x} Y{y} Z{z} A{a} B{b} C{c} F{speed}
        if is_relative:
            instruction = 'M20 G91 G1'
        if not speed:
            speed = self.default_speed
        if speed:
            speed = int(speed)

        pairings = {'X': x, 'Y': y, 'Z': z, 'A': a, 'B': b, 'C': c, 'F': speed}
        msg = self.generate_args_string(instruction, pairings)
        if is_com2:
            self.send_msg(com2_data=msg, wait_idle=True)
        else:
            self.send_msg(com1_data=msg, wait_idle=True)
        return True

    ### G代码指令转换---------
