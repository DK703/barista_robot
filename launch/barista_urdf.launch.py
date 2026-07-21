import os
from ament_index_python.packages import (get_package_prefix, get_package_share_directory)
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription)
from launch.substitutions import (PathJoinSubstitution, LaunchConfiguration)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import SetParameter
from launch_ros.actions import Node
from launch.substitutions import Command
# ROS2 Launch System will look for this function definition #
def generate_launch_description():

    # Get Package Directory #
    pkg_box_bot_gazebo = get_package_share_directory('barista_robot_description')
    pkg_box_bot_description = get_package_share_directory('barista_robot_description')
    gz_sim_pkg = get_package_share_directory("ros_gz_sim")

    # Set the Path to Robot Mesh Models for Loading in Gazebo Sim #
    # NOTE: Do this BEFORE launching Gazebo Sim #
    install_dir_path_gazebo = (get_package_prefix('barista_robot_description') + "/share")
    install_dir_path_description = (get_package_prefix('barista_robot_description') + "/share")
    gazebo_models_path = os.path.join(pkg_box_bot_gazebo, "models")
    description_meshes_path = os.path.join(pkg_box_bot_description, "meshes")
    gazebo_resource_paths = [install_dir_path_gazebo, install_dir_path_description, gazebo_models_path, description_meshes_path]
    if "GZ_SIM_RESOURCE_PATH" in os.environ:
        for resource_path in gazebo_resource_paths:
            if resource_path not in os.environ["GZ_SIM_RESOURCE_PATH"]:
                os.environ["GZ_SIM_RESOURCE_PATH"] += (':' + resource_path)
    else:
        os.environ["GZ_SIM_RESOURCE_PATH"] = (':'.join(gazebo_resource_paths))

    # Setup to launch the simulator and Gazebo world
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_pkg, 'launch', 'gz_sim.launch.py')),
            launch_arguments={'gz_args': [
            '-r ',  # <-- start unpaused
            PathJoinSubstitution([pkg_box_bot_gazebo, 'worlds', 'box_bot_empty.world'])
        ]}.items(),
    )

        ####### DATA INPUT ##########
    urdf_file = 'barista_robot_model.urdf'
    #xacro_file = "urdfbot.xacro"
    package_description = "barista_robot_description"

    ####### DATA INPUT END ##########
    print("Fetching URDF ==>")
    robot_desc_path = os.path.join(get_package_share_directory(package_description), "urdf", urdf_file)

    rviz_config = os.path.join(
        get_package_share_directory('barista_robot_description'),
        'rviz',
        'file.rviz'  
    )

    # Joint State Publisher_gui, different from reg joint state publisher
    joint_state_publisher_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        output="screen",
    )

    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher_node',
        emulate_tty=True,
        parameters=[{'use_sim_time': True, 'robot_description': Command(['xacro ', robot_desc_path])}],
        output="screen"
    )

    # Spawn the Robot #
    declare_spawn_model_name = DeclareLaunchArgument("model_name", default_value="my_robot",
                                                     description="Model Spawn Name")
    declare_spawn_x = DeclareLaunchArgument("x", default_value="0.0",
                                            description="Model Spawn X Axis Value")
    declare_spawn_y = DeclareLaunchArgument("y", default_value="0.0",
                                            description="Model Spawn Y Axis Value")
    declare_spawn_z = DeclareLaunchArgument("z", default_value="0.2",
                                            description="Model Spawn Z Axis Value")
    declare_spawn_yaw = DeclareLaunchArgument("yaw", default_value="3.14",
                                            description="Model Spawn Yaw Value")
    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        name="my_robot_spawn",
        arguments=[
            "-name", LaunchConfiguration("model_name"),
            "-allow_renaming", "true",
            "-topic", "robot_description",
            "-x", LaunchConfiguration("x"),
            "-y", LaunchConfiguration("y"),
            "-z", LaunchConfiguration("z"),
            "-Y", LaunchConfiguration("yaw"),
        ],
        output="screen",
    )

    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        arguments=[
            "/clock" + "@rosgraph_msgs/msg/Clock" + "[gz.msgs.Clock",
            "/cmd_vel" + "@geometry_msgs/msg/Twist" + "@gz.msgs.Twist",
            "/tf" + "@tf2_msgs/msg/TFMessage" + "[gz.msgs.Pose_V",
            "/odom" + "@nav_msgs/msg/Odometry" + "[gz.msgs.Odometry",
            "/joint_states" + "@sensor_msgs/msg/JointState" + "[gz.msgs.Model",
            "/scan" + "@sensor_msgs/msg/LaserScan" + "[gz.msgs.LaserScan",
        ],
        output="screen",
    )



    # Create and Return the Launch Description Object #
    return LaunchDescription(
        [
            # Sets use_sim_time for all nodes started below (doesn't work for nodes started from ignition gazebo) #
            SetParameter(name="use_sim_time", value=True),
            gz_sim,
            robot_state_publisher_node,
            joint_state_publisher_gui,
            Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            output='screen'
        ),
            SetParameter(name="use_sim_time", value=True),
            declare_spawn_model_name,
            declare_spawn_x,
            declare_spawn_y,
            declare_spawn_z,
            declare_spawn_yaw,
            gz_spawn_entity,
            gz_bridge,
        ]
    )
