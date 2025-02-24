'''
*
* Position tracking of magnet based on Finexus
* https://ubicomplab.cs.washington.edu/pdfs/finexus.pdf
*
*   - 3 Modes of operations
*       (1) Continuous sampling
*       (2) Continuous 3D live plot (BETA)
*       (2) Guided Point-by-Point
*
* VERSION: 0.3.2
*   - FIXED   : Program now does a check on the received data
*               to avoid the error we get so often regarding
*               the array containing invalid data
*   - MODIFIED: Streamlined code to make it more human friendly
*   - ADDED   : 3D plotting mode of operation
*   - ADDED   : Storring data now works under UNIX systems
*   - MODIFIED: Plotting now takes ~0.15s (previously ~0.30s)
*
* KNOWN ISSUES:
*   - Loss in accuracy in 3D space  (not even surprised)
*   - Data ouput is slow            (look into multithreading)
*   - 3D plotting is REALLY slow    (look into using animation instead of Axes3D)
*
* AUTHOR                    :   Edward Nichols
* LAST CONTRIBUTION DATE    :   Oct. 17th, 2017 Year of Our Lord
* 
* AUTHOR                    :   Mohammad Odeh 
* LAST CONTRIBUTION DATE    :   Nov. 13th, 2017 Year of Our Lord
*
'''

# Import Modules
import matplotlib                                       # Import matplotlib first as to be able to ...
matplotlib.use('GTKAgg')                                # ... change the backend for the subsequent imports
import  numpy                   as      np              # Import Numpy
import  matplotlib.pyplot       as      plt             # 2D plotting
from    mpl_toolkits.mplot3d    import  Axes3D          # 3D plotting
from    time                    import  sleep, clock    # Sleep for stability, clock for profiling
from    scipy.optimize          import  root            # Solve System of Eqns for (x, y, z)
from    scipy.linalg            import  norm            # Calculate vector norms (magnitude)
from    usbProtocol             import  createUSBPort   # Create USB port (serial comm. w\ Arduino)
from    threading               import  Thread          # Used to thread processes
from    Queue                   import  Queue           # Used to queue input/output
import  os, platform                                    # Directory/file manipulation

# ************************************************************************
# =====================> DEFINE NECESSARY FUNCTIONS <====================*
# ************************************************************************


def argsort( seq ):
    '''
    Sort a list's elements from smallest to largest and
    return the sorted INDICES NOT VALUES!
    
    INPUTS:
        - seq: A list whose elements are to be sorted 

    OUTPUT:
        - A list containing the indices of the given list's elements
          arranged from the index of the element with the smallest
          value to the index of the element with the largest value
    '''
    # http://stackoverflow.com/questions/3071415/efficient-method-to-calculate-the-rank-vector-of-a-list-in-python
    return sorted(range(len(seq)), key=seq.__getitem__)

# --------------------------

def bubbleSort( arr, N ):
    '''
    Sort a list's elements from smallest to largest 
    
    INPUTS:
        - arr: List to be sorted
        - N  : Number of elements in said list that need to be sorted
                (i.e list has 5 elements, if N=3, sort the first 3)

    OUTPUT:
        - A sorted list of size N
    '''
    data = []
    for i in range(0, N):
        data.append( arr[i] )

    for i in range(0, len(data)):
        for j in range(0, len(data)-i-1):
            if (data[j] > data[j+1]):
                temp = data[j]
                data[j] = data[j+1]
                data[j+1] = temp
            else:
                continue
    return (data)

# --------------------------

def getData( ser ):
    '''
    Pool the data from the MCU (wheteher it be a Teensy or an Arduino or whatever)
    The data consists of the magnetic field components in the x-, y-, and z-direction
    of all the sensors. The array must begin with '<' as the SOH signal, the compononents
    must be comma delimited, and must end with '>' as the EOT signal.
    
            >$\     <B_{1x}, B_{1y}, B_{1z}, ..., B_{1x}, B_{1y}, B_{1z}> 
    
    INPUTS:
        - ser: a serial object. Note that the serial port MUST be open before
               passing it the to function

    OUTPUT:
        - Individual numpy arrays of all the magnetic field vectors
    '''
    global CALIBRATING

    # Flush buffer
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # Allow data to fill-in buffer
    # sleep(0.1)

    try:
        # Wait for the sensor to calibrate itself to ambient fields.
        while( True ):
            if(CALIBRATING == True):
                print( "Calibrating...\n" )
                CALIBRATING = False
            if ser.in_waiting > 0:  
                inData = ser.read()  
                if inData == '<':
                    break  

        # Read the actual data value. Stop at End of Data specifier '>'. 
        line = ''
        while( True ):
            if ser.in_waiting > 0:
                inData = ser.read()
                if inData == '>':
                    break
                line = line + inData

        # Split line into the constituent components
        col     = (line.rstrip()).split(",")

        # Check if array is corrupted
        if (len(col) == 18):
            #
            # Construct magnetic field array
            #

            # Sensor 1
            Bx = float( col[0] )
            By = float( col[1] )
            Bz = float( col[2] )
            B1 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 2
            Bx = float( col[3] )
            By = float( col[4] )
            Bz = float( col[5] )
            B2 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 3
            Bx = float( col[6] )
            By = float( col[7] )
            Bz = float( col[8] )
            B3 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 4
            Bx = float( col[9]  )
            By = float( col[10] )
            Bz = float( col[11] )
            B4 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 5
            Bx = float( col[12] )
            By = float( col[13] )
            Bz = float( col[14] )
            B5 = np.array( ([Bx],[By],[Bz]), dtype='float64') # Units { G }

            # Sensor 6
            Bx = float( col[15] )
            By = float( col[16] )
            Bz = float( col[17] )
            B6 = np.array( ([Bx],[By],[Bz]), dtype='float64' )# Units { G }
            
            # Return vectors
            return ( B1, B2, B3, B4, B5, B6 )

        # In case array is corrupted, call the function again
        else:
            return( getData(ser) )

    except Exception as e:
        print( "Caught error in getData()"      )
        print( "Error type %s" %str(type(e))    )
        print( "Error Arguments " + str(e.args) )

# --------------------------

def LHS( root, K, norms ):
    '''
    Construct the left hand side (LHS) of the equations
    to numerically solve for.
    Recall that in order to solve a system numerically it
    must have the form of,
    
                >$\  f(x, y, z, ...) = LHS = 0
    
    INPUTS:
        - root  : a numpy array contating the initial guesses of the roots
        - K     : K is a property of the magnet and has units of { G^2.m^6}
        - norms : An array/list of the vector norms of the magnetic field
                  vectors for all the sensors

    OUTPUT:
        - An array of equations that are sorted corresponding to which
          3 sensors' equations are going to be used with the LMA solver.
          The sorting is based on which 3 sensors are closest to the magnet.
    '''
    global PRINT
    
    # Extract x, y, and z
    x, y, z = root
    
    # Construct the (r) terms for each sensor
    # NOTE: Relative distance terms are in meters
    #     : Standing on sensor(n), how many units in
    #       the x/y/z direction should I march to get
    #       back to sensor1 (origin)?
    r1 = float( ( (x+0.000)**2. + (y+0.000)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 1 (ORIGIN)
    r2 = float( ( (x+0.000)**2. + (y-0.125)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 2
    r3 = float( ( (x-0.100)**2. + (y+0.050)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 3
    r4 = float( ( (x-0.100)**2. + (y-0.175)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 4
    r5 = float( ( (x-0.200)**2. + (y+0.000)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 5
    r6 = float( ( (x-0.200)**2. + (y-0.125)**2. + (z+0.00)**2. )**(1/2.) )  # Sensor 6

    # Construct the equations
    Eqn1 = ( K*( r1 )**(-6.) * ( 3.*( z/r1 )**2. + 1 ) ) - norms[0]**2.     # Sensor 1
    Eqn2 = ( K*( r2 )**(-6.) * ( 3.*( z/r2 )**2. + 1 ) ) - norms[1]**2.     # Sensor 2
    Eqn3 = ( K*( r3 )**(-6.) * ( 3.*( z/r3 )**2. + 1 ) ) - norms[2]**2.     # Sensor 3
    Eqn4 = ( K*( r4 )**(-6.) * ( 3.*( z/r4 )**2. + 1 ) ) - norms[3]**2.     # Sensor 4
    Eqn5 = ( K*( r5 )**(-6.) * ( 3.*( z/r5 )**2. + 1 ) ) - norms[4]**2.     # Sensor 5
    Eqn6 = ( K*( r6 )**(-6.) * ( 3.*( z/r6 )**2. + 1 ) ) - norms[5]**2.     # Sensor 6

    # Construct a vector of the equations
    Eqns = [Eqn1, Eqn2, Eqn3, Eqn4, Eqn5, Eqn6]

    # Determine which sensors to use based on magnetic field value (smallValue==noBueno!)
    sort = argsort( norms )             # Auxiliary function sorts norms from smallest to largest
    sort.reverse()                      # Python built-in function reverses elements of list
    f=[]                                # Declare vector to hold relevant functions

    for i in range(0, 3):               # Fill functions' array with the equations that correspond to
        f.append( Eqns[sort[i]] )       # the sensors with the highest norm, thus closest to magnet
        
    # Return vector
    return ( f )

# --------------------------

def findIG( magFields ):
    '''
    Dynamic search of initial guess for the LMA solver based on magnitude
    of the magnetic field relative to all the sensors.
    A high magnitude reading indicates magnet is close to some 3
    sensors, the centroid of the traingle created by said sensors
    is fed as the initial guess
    
    INPUTS:
        - magfield: a numpy array containing all the magnetic field readings

    OUTPUT:
        - A numpy array containing <x, y, z> values for the initial guess
    '''
    
    # Define IMU positions on the grid
    #      / sensor 1: (x, y, z)
    #     /  sensor 2: (x, y, z)
    # Mat=      :          :
    #     \     :          :
    #      \ sensor 6: (x, y, z)
    IMU_pos = np.array(((0.0  , 0.0  ,   0.0) ,
                        (0.0  , 0.125,   0.0) ,
                        (0.100,-0.050,   0.0) ,
                        (0.100, 0.175,   0.0) ,
                        (0.200, 0.0  ,   0.0) ,
                        (0.200, 0.125,   0.0)), dtype='float64')

    # Read current magnetic field from MCU
    (H1, H2, H3, H4, H5, H6) = magFields

    # Compute L2 vector norms
    HNorm = [ float( norm(H1) ), float( norm(H2) ),
              float( norm(H3) ), float( norm(H4) ),
              float( norm(H5) ), float( norm(H6) ) ]
    
    # Determine which sensors to use based on magnetic field value (smallValue==noBueno!)
    sort = argsort( HNorm )             # Auxiliary function sorts norms from smallest to largest
    sort.reverse()                      # Python built-in function reverses elements of list

    IMUS = bubbleSort( sort, 3 )

    # Return the initial guess as the centroid of the detected triangle
    return ( np.array(((IMU_pos[IMUS[0]][0]+IMU_pos[IMUS[1]][0]+IMU_pos[IMUS[2]][0])/3.,
                       (IMU_pos[IMUS[0]][1]+IMU_pos[IMUS[1]][1]+IMU_pos[IMUS[2]][1])/3.,
                       (IMU_pos[IMUS[0]][2]+IMU_pos[IMUS[1]][2]+IMU_pos[IMUS[2]][2])/3. -0.01), dtype='float64') )

# --------------------------

def storeData( data ):
    '''
    Store computed position co-ordinates into a .txt file
    
    INPUTS:
        - data: A list containing all the computed co-ordinate points
    '''
    
    print( "Storing data log under data.txt" )
            
    if platform.system()=='Windows':

        # Define useful paths
        homeDir = os.getcwd()
        dst     = homeDir + '\\output'
        dataFile= dst + '\\data.txt'

    elif platform.system()=='Linux':

        # Define useful paths
        homeDir = os.getcwd()
        dst = homeDir + '/output'
        dataFile= dst + '/data.txt'
    
    # Check if directory exists
    if ( os.path.exists(dst)==False ):
        # Create said directory
        os.makedirs(dst)

    # Write into file
    for i in range( 0, len(data) ):
            with open( dataFile, "a" ) as f:
                f.write(str(data[i][0]) + "," + str(data[i][1]) + "," + str(data[i][2]) + "," + str(data[i][3]) + "\n")

    print( "DONE!" )

# --------------------------

def plotPos( actual, calculated ):
    '''
    2D plotting of computed values juxtaposed on the xy-plane.
    Plots actual vs measured position
    
    INPUTS:
        - actual    : an array/list containing the actual xy co-ordinates
        - calculated: an array/list containing the computed xy co-ordinates
    '''
    
    data = ( actual, calculated )
     
    # Create plot
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, facecolor="1.0")


    # major ticks every 5, minor ticks every 1                                      
    major_ticks = np.arange(20, 116, 5)                                              
    minor_ticks = np.arange(20 ,116, 1)                                               

    ax.set_xticks( major_ticks )                                                       
    ax.set_xticks( minor_ticks, minor=True )                                           
    ax.set_yticks( major_ticks )                                                       
    ax.set_yticks( minor_ticks, minor=True )

    # Set xy-axes scale + labels
    ax.set_xlim( [30, 115] )
    ax.set_ylim( [20, 105] )
    ax.set_xlabel( 'Distance (mm)' )
    ax.set_ylabel( 'Distance (mm)' )

    # Add a grid                                                       
    ax.grid( which='both' )                                                            

    # Modify transperancy settings for the grids:                               
    ax.grid( which='minor', alpha=0.2 )                                                
    ax.grid( which='major', alpha=0.5 )

    # Extract data
    x_actual = []
    y_actual = []
    x_calc = []
    y_calc = []
    for i in range( 0,len(actual) ):
        x_actual.append( actual[i][0] )
        y_actual.append( actual[i][1] )
        x_calc.append( calculated[i][0] )
        y_calc.append( calculated[i][1] )
    ax.scatter( x_actual, y_actual, alpha=0.8, color='r', s=30, label="Actual" )
    ax.scatter( x_calc, y_calc, alpha=0.8, color='g', s=30, label="Calculated" )

    # Annotate data points
    for i, j, k, l in zip( x_calc, y_calc, x_actual, y_actual ):
        ax.annotate('($\Delta x=%.2f, \Delta y=%.2f$)'%(abs(i-k),abs(j-l)), xy=(i, j+0.5))
    
    plt.title( 'Actual vs Calculated Position' )
    plt.legend(loc=2)
    plt.show()

# --------------------------

def plot_3D( pos, ax ):
    '''
    3D plotting of computed values in a virtual box.
    INPUTS:
        - xyz: an array/list containing the x-, y-, and z- co-ordinates
        - ax : matplotlib Axes3D() object
    '''
    ax.set_xlim3d(   0, 175 )
    ax.set_ylim3d( -25, 150 )
    ax.set_zlim3d(   0, 200 )
    ax.set_xlabel( 'X Position (mm)' )
    ax.set_ylabel( 'Y Position (mm)' )
    ax.set_zlabel( 'Z Position (mm)' )
    ax.set_title( '3D Tracking' )
    ax.scatter( float(pos[0]), float(pos[1]), float(pos[2]) )
    plt.draw()
    plt.pause(0.0001)
    ax.cla()

# ************************************************************************
# ===========================> SETUP PROGRAM <===========================
# ************************************************************************

# Useful variables
global CALIBRATING

CALIBRATING = True                              # Boolean to indicate that device is calibrating
READY       = False                             # Give time for user to place magnet

#K           = 7.27e-8                           # Small magnet's constant   (K) || Units { G^2.m^6}
K           = 1.09e-6                           # Big magnet's constant     (K) || Units { G^2.m^6}
dx          = 1e-7                              # Differential step size (Needed for solver)
calcPos     = []                                # Empty array to hold calculated positions


# Establish connection with Arduino
DEVC = "Arduino"                                # Device Name (not very important)
PORT = 4                                        # Port number (VERY important)
BAUD = 115200                                   # Baudrate    (VERY VERY important)

# Error handling in case serial communcation fails (1/2)
try:
    IMU = createUSBPort( DEVC, PORT, BAUD )     # Create serial connection
    if IMU.is_open == False:                    # Make sure port is open
        IMU.open()
    print( "Serial Port OPEN" )

    initialGuess = findIG( getData(IMU) )       # Determine initial guess based on magnet's location

# Error handling in case serial communcation fails (2/2)
except Exception as e:
    print( "Could NOT open serial port" )
    print( "Error type %s" %str(type(e)) )
    print( "Error Arguments " + str(e.args) )
    sleep( 2.5 )
    quit()                                      # Shutdown entire program

# ************************************************************************
# =========================> MAKE IT ALL HAPPEN <=========================
# ************************************************************************

# Choose mode of operation
print( "Choose plotting mode:" )                # ...
print( "1. Point-by-Point." )                   # Inform user of all the possible
print( "2. 2D Continuous." )                    # plotting modes
print( "3. 3D Continuous." )                    # ...

mode = raw_input(">\ ")                         # Wait for user input

# --------------------------------------------------------------------------------------

# If point-by-point mode was selected:
if ( mode == '1' ):

    # Array of points on grid to plot against
    actualPos = [ [50 ,  25],
                  [50 ,  50],
                  [50 ,  75],
                  [50 , 100],
                  [75 ,  25],
                  [75 ,  50],
                  [75 ,  75],
                  [75 , 100],
                  [100,  25],
                  [100,  50],
                  [100,  75],
                  [100, 100],
                  [125,  25],
                  [125,  50],
                  [125,  75],
                  [125, 100] ]

    i=0
    while (i is not(len(actualPos)) ):
        
        print( "Place magnet at " + str(actualPos[i]) + "mm" )
        sleep( 1.5 )                                                        # Sleep for stability

        var = raw_input("Ready? (Y/N): ")                                   # Wait for user to be ready

        if (var=='y' or var=='Y'):
            print( "Collecting data!" )

            # Pool data from Arduino
            (H1, H2, H3, H4, H5, H6) = getData(IMU)                         # Pool data from MCU
            initialGuess = findIG( getData(IMU) )                           # Get current initial guess
            
            # Compute norms
            HNorm = [ float(norm(H1)), float(norm(H2)),                     #
                      float(norm(H3)), float(norm(H4)),                     # Compute L2 vector norms
                      float(norm(H5)), float(norm(H6)) ]                    #
            
            # Solve system of equations
            sol = root(LHS, initialGuess, args=(K, HNorm), method='lm',     # Invoke solver using the
                       options={'ftol':1e-10, 'xtol':1e-10, 'maxiter':1000, # Levenberg-Marquardt 
                                'eps':1e-8, 'factor':0.001})                # Algorithm (aka LMA)

            # Print solution (coordinates) to screen
            pos = [sol.x[0]*1000, sol.x[1]*1000, -1*sol.x[2]*1000]
            print( "(x, y, z): (%.3f, %.3f, %.3f)" %(pos[0], pos[1], pos[2]) )
            
            sleep( 0.1 )                                                    # Sleep for stability

            # Check if solution makes sense
            if (abs(sol.x[0]*1000) > 500) or (abs(sol.x[1]*1000) > 500) or (abs(sol.x[2]*1000) > 500):
                print("NOT STORED\n\n")                                     # Inform user that the data point was NOT stored
                initialGuess = findIG( getData(IMU) )                       # Determine initial guess based on magnet's location
                
            # Update initial guess with current position and feed back to solver
            else:
                calcPos.append( pos )                                       # Append calculated position to list
                print("STORED\n\n")                                         # Inform user that the data point was stored
                i = i+1                                                     # Move on to next point

    # Post processing        
    storData( calcPos )                                                     # Write data points to a .txt file
    plotPos( actualPos, calcPos )                                           # Juxtapose actual vs computed data on 2D plot

# --------------------------------------------------------------------------------------
    
# If 2D continuous mode was selected:
elif ( mode == '2' ):
    
    print( "\n******************************************" )
    print( "*NOTE: Press Ctrl-C to save data and exit." )
    print( "******************************************\n" )

    while ( True ):
        try:
            # Inform user that system is almost ready
            if(READY == False):
                print( "Place magnet on track" )
                sleep( 2.5 )
                print( "Ready in 3" )
                sleep( 1.0 )
                print( "Ready in 2" )
                sleep( 1.0 )
                print( "Ready in 1" )
                sleep( 1.0 )
                print( "GO!" )
                start = clock()

                # Set the device to ready!!
                READY = True

            # Data acquisition
            (H1, H2, H3, H4, H5, H6) = getData(IMU)                         # Get data from MCU
            
##            # Check if queue has something available for retrieval
##            if Q_getData.qsize() > 0:
##                # Pool data from Arduino
##                (H1, H2, H3, H4, H5, H6) = Q_getData.get()
            
            # Compute norms
            HNorm = [ float(norm(H1)), float(norm(H2)),                     #
                      float(norm(H3)), float(norm(H4)),                     # Compute L2 vector norms
                      float(norm(H5)), float(norm(H6)) ]                    #
            
            # Solve system of equations
            sol = root(LHS, initialGuess, args=(K, HNorm), method='lm',     # Invoke solver using the
                       options={'ftol':1e-10, 'xtol':1e-10, 'maxiter':1000, # Levenberg-Marquardt 
                                'eps':1e-8, 'factor':0.001})                # Algorithm (aka LMA)

            # Print solution (coordinates) to screen
            pos = [sol.x[0]*1000, sol.x[1]*1000, -1*sol.x[2]*1000, float(clock())]
            print( "(x, y, z): (%.3f, %.3f, %.3f) Time: %.3f" %(pos[0], pos[1], pos[2], pos[3]) )
            
            # Check if solution makes sense
            if (abs(sol.x[0]*1000) > 500) or (abs(sol.x[1]*1000) > 500) or (abs(sol.x[2]*1000) > 500):
                initialGuess = findIG( getData(IMU) )                       # Determine initial guess based on magnet's location
                
            # Update initial guess with current position and feed back to solver
            else:
                calcPos.append( pos )                                       # Append calculated position to list
                
                initialGuess = np.array( (sol.x[0]+dx, sol.x[1]+dx,         # Update the initial guess as the
                                          sol.x[2]+dx), dtype='float64' )   # current position and feed back to LMA

        # Save data on EXIT
        except KeyboardInterrupt:
            storeData( calcPos )                                            # Store data in a log file
            break                                                           # Exit loop 43va!

# --------------------------------------------------------------------------------------

# Else if 3D continuous mode was selected:
if ( mode == '3' ):

    # Setup 3D box for plotting
    plt.ion()                                   # Interactive mode (aka animated, aka live)
    fig = plt.figure( figsize =                 # figaspect(0.5) makes the figure twice as wide as it is tall
                      plt.figaspect(0.5)*1.5 )  # *1.5 increases the size of the figure.
    ax = Axes3D( fig )                          # Create figure
    
    print( "\n******************************************" )
    print( "*NOTE: Press Ctrl-C to save data and exit." )
    print( "******************************************\n" )

    while ( True ):
        try:
            # Inform user that system is almost ready
            if(READY == False):
                print( "Place magnet on track" )
                sleep( 2.5 )
                print( "Ready in 3" )
                sleep( 1.0 )
                print( "Ready in 2" )
                sleep( 1.0 )
                print( "Ready in 1" )
                sleep( 1.0 )
                print( "GO!" )
                start = clock()

                # Set the device to ready!!
                READY = True

            # Data acquisition
            (H1, H2, H3, H4, H5, H6) = getData(IMU)                         # Get data from MCU

            # Compute norms
            HNorm = [ float(norm(H1)), float(norm(H2)),                     #
                      float(norm(H3)), float(norm(H4)),                     # Compute L2 vector norms
                      float(norm(H5)), float(norm(H6)) ]                    #
            
            # Solve system of equations
            sol = root(LHS, initialGuess, args=(K, HNorm), method='lm',     # Invoke solver using the
                       options={'ftol':1e-10, 'xtol':1e-10, 'maxiter':1000, # Levenberg-Marquardt 
                                'eps':1e-8, 'factor':0.001})                # Algorithm (aka LMA)

            # Print solution (coordinates) to screen
            pos = [sol.x[0]*1000, sol.x[1]*1000, -1*sol.x[2]*1000, float(clock())]
            print( "(x, y, z): (%.3f, %.3f, %.3f) Time: %.3f" %(pos[0], pos[1], pos[2], pos[3]) )

            plot_3D( pos, ax )                                              # Plot the computed position

            # Check if solution makes sense
            if (abs(sol.x[0]*1000) > 500) or (abs(sol.x[1]*1000) > 500) or (abs(sol.x[2]*1000) > 500):
                initialGuess = findIG( getData(IMU) )                       # Determine initial guess based on magnet's location
                
            # Update initial guess with current position and feed back to solver
            else:
                calcPos.append( pos )                                       # Append calculated position to list
                
                initialGuess = np.array( (sol.x[0]+dx, sol.x[1]+dx,         # Update the initial guess as the
                                          sol.x[2]+dx), dtype='float64' )   # current position and feed back to LMA

        # Save data on EXIT
        except KeyboardInterrupt:
            storeData( calcPos )                                            # Store data in a log file
            break                                                           # Exit loop 43va!

# --------------------------------------------------------------------------------------

else:
    print( "Really?? Restart script 'cause I ain't doing it for you" )
# ************************************************************************
# =============================> DEPRECATED <=============================
# ************************************************************************
#
