from constants import *
from food import *
from abstract import ParentSprite
from nn import NN
import numpy as np
import math
import pygame


class Blob(ParentSprite):
    """ 
    Represents a blob in the natural/articifial evolution simulation
    """


    def __init__(self, nn=None):
        """ 
        Initialize blob by inheriting ParentSprite and assigning attributes

        Args:
            nn (class): can pass in the neural net from another blob
        """
        super(Blob, self).__init__() # values are not needed
        self.int_center = int(self.center_x), int(self.center_y)
        self.radius = 15.0
        self.angle = random.uniform(0,2*np.pi)
        self.energy = MAX_ENERGY
        self.alive = True
        self.food_eaten = 0
        self.score_int = 0

        ######################

        self.color = np.random.randint(256, size=3)

        self.wheel_radius = 1.50
        self.axle_length = 1.0 * (2 * self.radius)
        self.left_wheel_rotation  = 0.0
        self.right_wheel_rotation = 0.0

        self.max_wheel_angular_velocity = np.pi / 564 # max pixel displacement per time step
        self.max_rotation = np.pi / 20

        # visual input variables
        self.eye_position = np.pi / 7 # angle from direction they're facing
        self.eye_peripheral_width = np.pi / 4 # angle from center of eye's vision to edge of peripheral
        self.max_visable_distance = 8 * self.radius # how far the eye can see
        self.eye_data = {'left_eye':{'pos':[0,0], 'left_peripheral': [0,0], 'right_peripheral': [0,0]}, 
                        'right_eye':{'pos':[0,0], 'left_peripheral': [0,0], 'right_peripheral': [0,0]}}
        self.visual_input = {'left_eye':[0.0, 0.0, 0.0],  # left eye:  red, green, blue
                            'right_eye':[0.0, 0.0, 0.0]}  # right eye: red, green, blue   
        self.left_arcs, self.right_arcs = [], [] # list of arcs of what the blob sees

        ######################

        ########## TEST VARIABLES ############

        self.left_eye_pos  = (0,0)
        self.right_eye_pos = (0,0)
        self.p_left  = (10,10)
        self.p_right = (20,20)
        self.f = (30,30)
        self.l1 = 5

        ######################################

        self.last_angle = .01 # IS THIS EVEN USED?

        #scoring related
        self.dist_moved = 0

        # Neural Network stuff here:
        if nn is not None:
            self.nn = NN(((1, nn),))
        else:
            self.nn = NN()


    def out_of_bounds(self):
        """ 
        updates self.angle so it is always between -2pi and +2pi
        """

        if self.angle > 2 * np.pi:
            self.angle = self.angle % (2 * np.pi)
        if self.angle < -2 * np.pi:
            self.angle = -self.angle % (2 * np.pi)

    # this is the old way of inputting sight, its causes the program to run very slowly
    def update_input(self, model):
        
        self.update_sight(model)
        #self.print_input()
    def print_input(self):
        print 'Eyes:\tLeft RGB: [%.3f, %.3f, %.3f] Right RGB: [%.3f, %.3f, %.3f]' \
         % (self.visual_input['left_eye'][0], \
            self.visual_input['left_eye'][1], \
            self.visual_input['left_eye'][2], \
            self.visual_input['right_eye'][0], \
            self.visual_input['right_eye'][1], \
            self.visual_input['right_eye'][2])
        print 'Energy:\t%f' % self.energy
        print ''

    def old_update_sight(self):

        # variable setup
        x, y, r, theta = self.center_x, self.center_y, self.radius, self.angle
        eye_sep = self.eye_position
        vis_dist = self.max_visable_distance
        periph_angle = self.eye_peripheral_width
        
        # reset input 
        lr, lg, lb, rr, rg, rb = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

        # LEFT EYE
        
        # get left field of vision
        left_eye_pos = [x + r * np.cos(theta - eye_sep), y + r * np.sin(theta - eye_sep)]
        far_outer_left_peripheral = (left_eye_pos[0] + vis_dist * np.cos(theta - eye_sep - periph_angle), \
                                     left_eye_pos[1] + vis_dist * np.sin(theta - eye_sep - periph_angle))
        far_inner_left_peripheral = (left_eye_pos[0] + vis_dist * np.cos(theta - eye_sep + periph_angle), \
                                     left_eye_pos[1] + vis_dist * np.sin(theta - eye_sep + periph_angle))

        # analysis left field of vision
        num_angles = 2 * r
        num_pts_per_ray = 2 * r
        angles = np.linspace((theta - eye_sep - periph_angle), (theta - eye_sep + periph_angle), num_angles)
        vis_depth = np.linspace(3.5 * r / 8, vis_dist, num_pts_per_ray)
        self.left_eye_points_seen = []
        for angle in angles:
            for i in vis_depth:
                px, py = int(left_eye_pos[0] + i * np.cos(angle)), int(left_eye_pos[1] + i * np.sin(angle))
                if px >= SCREEN_SIZE[0] or px < 0 or py >= SCREEN_SIZE[1] or py < 0:
                    pixel_color = [0,0,0,0]
                else:
                    pixel_color = view.screen.get_at((px, py))
                #print 'i = %d, angle = %f, px=%f, py=%f, pixel_color = %s' % (i, angle, px, py, pixel_color)
                self.left_eye_points_seen.append((px,py))
                if pixel_color != (0,0,0,255):
                    lr += pixel_color[0]
                    lg += pixel_color[1]
                    lb += pixel_color[2]
                    break

        lr /= (255 * num_angles)
        lg /= (255 * num_angles)
        lb /= (255 * num_angles)
        self.visual_input['left_eye'] = [lr, lg, lb]
        
        # RIGHT EYE
        right_eye_pos = (x + r * np.cos(theta + eye_sep), y + r * np.sin(theta + eye_sep))
        far_outer_right_peripheral = (right_eye_pos[0] + vis_dist * np.cos(theta + eye_sep - periph_angle), \
                                      right_eye_pos[1] + vis_dist * np.sin(theta + eye_sep - periph_angle))
        far_inner_right_peripheral = (right_eye_pos[0] + vis_dist * np.cos(theta + eye_sep + periph_angle), \
                                      right_eye_pos[1] + vis_dist * np.sin(theta + eye_sep + periph_angle))

        # analysis right field of vision
        angles = np.linspace((theta + eye_sep - periph_angle), (theta + eye_sep + periph_angle), num_angles)
        vis_depth = np.linspace(1.75 * r / 8, vis_dist, num_pts_per_ray)
        self.right_eye_points_seen = []
        for angle in angles:
            for i in vis_depth:
                px, py = int(right_eye_pos[0] + i * np.cos(angle)), int(right_eye_pos[1] + i * np.sin(angle))
                #print (px, py)
                if px >= SCREEN_SIZE[0] or px < 0 or py >= SCREEN_SIZE[1] or py < 0:
                    pixel_color = [0,0,0,0]
                else:
                    pixel_color = view.screen.get_at((px, py))
                #print 'i = %d, angle = %f, px=%f, py=%f, pixel_color = %s' % (i, angle, px, py, pixel_color)
                self.right_eye_points_seen.append((px,py))
                if pixel_color != (0,0,0,255):
                    rr += pixel_color[0]
                    rg += pixel_color[1]
                    rb += pixel_color[2]
                    break

        rr /= (255 * num_angles)
        rg /= (255 * num_angles)
        rb /= (255 * num_angles)
        self.visual_input['right_eye'] = [rr, rg, rb]
        

        # draw points that were analyzed
        #for pt in self.left_eye_points_seen:
        #   pygame.draw.circle(surface, [255,0,0], pt, 1)

        # draw points that were analyzed
        #for pt in self.right_eye_points_seen:
        #   pygame.draw.circle(surface, [0,255,0], pt, 1)

    # input sight
    def update_sight(self, model):


        # LEFT EYE
        # get left field of vision
        self.update_eye_data('left_eye')

        # get the arcs in the left field of view
        self.left_arcs = self.update_visual_field(model.blobs + model.foods, 'left_eye')
        
        # get rgb for left eye
        self.update_eye_rgb(self.left_arcs, 'left_eye')


        # RIGHT EYE
        # get left field of vision
        self.update_eye_data('right_eye')

        # get the arcs in the right field of view
        self.right_arcs = self.update_visual_field(model.blobs + model.foods, 'right_eye')
        
        # get rgb for right eye
        self.update_eye_rgb(self.right_arcs, 'right_eye')
    def update_eye_data(self, eye):

        # general variable setup
        x, y, r, theta = self.center_x, self.center_y, self.radius, self.angle
        
        # eye variable setup
        eye_sep = self.eye_position
        vis_dist = self.max_visable_distance
        periph_angle = self.eye_peripheral_width
        
        if eye == 'left_eye': e = -1
        else: e = 1 # right eye
        eye_pos = [x + r * np.cos(theta + e*eye_sep), y + r * np.sin(theta +e*eye_sep)]
        self.eye_data[eye]['pos'] = (eye_pos[0], eye_pos[1])
        self.eye_data[eye]['left_peripheral'] = \
            (eye_pos[0] + vis_dist * np.cos(theta + e*eye_sep - periph_angle), \
             eye_pos[1] + vis_dist * np.sin(theta + e*eye_sep - periph_angle))
        self.eye_data[eye]['right_peripheral'] = \
            (eye_pos[0] + vis_dist * np.cos(theta + e*eye_sep + periph_angle), \
             eye_pos[1] + vis_dist * np.sin(theta + e*eye_sep + periph_angle))
    def update_visual_field(self, circles, eye):

        # find the outer edge points of the arc of c that is visable from eye_pos
        # point perpendicular to surface of circle that makes line with eye
        
        eye_pos = self.eye_data[eye]['pos']
        left_peripheral = self.eye_data[eye]['left_peripheral'] 
        right_peripheral = self.eye_data[eye]['right_peripheral']

        vision_opaquness = 25 # how opaque the view draws the arcs of the vision (0 to 255)
        arcs = [{ # start with just 1 empty field of vision
        'left_side':left_peripheral, # left_side = the point on the 
        'right_side':right_peripheral,
        'd':self.max_visable_distance, # distance from eye to arc
        'color':[255,255,255,vision_opaquness], # opaque white
        'empty':True # if the arc represents empty space or a circle
        }]

        for c in circles:

            if c == self: continue

            cx, cy, cr = c.center_x, c.center_y, c.radius
            self.f = (int(cx), int(cy))
            ex, ey = eye_pos[0], eye_pos[1]

            # d = distance from eye_pos to center of c
            dx, dy = cx - ex, cy - ey
            d = np.sqrt(dx**2 + dy**2)

            # if its within the blob's vision
            if d - cr <= self.max_visable_distance:

                # p_left = the point on the edge of circle c that is
                # forms a line tangent to c when connected to eye_pos.
                # p_left is on the left edge of the circle when viewed from eye_pos
                a = np.arctan2(dy,dx) # a = angle between horizontal line and line from eye_pos to c                    
                a2 = np.arcsin(cr/d) # a2 = angle between line from eye_pos to c and line from eye_pos to p_left
                d2 = np.sqrt(d**2 - cr**2) # d2 = distance from eye_pos to p_left
                # if the circle c is just barely on the outside of the max_visable_distane
                if d2 > self.max_visable_distance:
                    d2 = self.max_visable_distance
                    a2 = np.arccos((d2**2 + d**2 - cr**2)/(2*d2*d))
                p_left = (ex + d2*np.cos(a-a2), ey + d2*np.sin(a-a2))
                
                # if p_left is on the left side of right periferal
                if self.left_side(eye_pos, right_peripheral, p_left):

                    #self.p_left  = (int(p_left[0]),  int(p_left[1])) # FOR TESTING PURPOSES 

                    # p_right = the point on the edge of circle c that is
                    # forms a line tangent to c when connected to eye_pos.
                    # p_right is on the right edge of the circle when viewed from eye_pos
                    p_right = (ex + d2*np.cos(a+a2), ey + d2*np.sin(a+a2))

                    # if p_right is on the right side of left periferal
                    if self.right_side(eye_pos, left_peripheral, p_right):

                        col = [c.color[0], c.color[1], c.color[2], vision_opaquness]
                        first_arc, last_arc = True, False # first and last arc in the iteration
                        original_arcs = []
                        for a in arcs: original_arcs.append(a)
                        i = -1
                        for a in original_arcs:

                            i += 1
                            #print 'i=%d, len(arcs)=%d' % (i, len(arcs))
                            if arcs[i]['color'] == col and arcs[i]['d'] == d2: i += 1
                            if i > 0: first_arc = False
                            if i == len(arcs)-1: last_arc = True

                            a_left, a_right = a['left_side'], a['right_side']

                            LPLL = self.left_side(eye_pos, a_left, p_left)
                            LPRL = not LPLL
                            LPLR = self.left_side(eye_pos, a_right, p_left)
                            LPRR = not LPLR
                            RPLL = self.left_side(eye_pos, a_left, p_right)
                            RPRL = not RPLL
                            RPLR = self.left_side(eye_pos, a_right, p_right)
                            RPRR = not RPLR

                            a_d = a['d']
                            closer = d - cr < a_d

                            if closer:
                                #print '%s is closer than arc[%d]:%s' % (col, i, arcs[i]['color'])
                                #print 'LPLL=%s, LPRL=%s, LPLR=%s, LPRR=%s, RPLL=%s, RPRL=%s, RPLR=%s, RPRR=%s' \
                                #% (LPLL, LPRL, LPLR, LPRR, RPLL, RPRL, RPLR, RPRR)

                                if LPLL and RPLL or LPRR and RPRR:
                                    # senario where none of arc a is not overlapped by c
                                    #print '%s none of arc[%d]:%s' % (col, i, arcs[i]['color'])
                                    pass

                                elif LPRL and LPLR and RPRR:
                                    # senario where the right side of arc a is overlapped by c
                                    #print '%s right of arc[%d]:%s' % (col, i, arcs[i]['color'])

                                    # so move arc a's right side in
                                    arcs[i]['right_side'] = p_left

                                    # and insert it starting at the right side of arc a
                                    arcs.insert(i+1, {
                                        'left_side':p_left,
                                        'right_side':a_right,
                                        'd':d2,
                                        'color':col,
                                        'empty':False
                                    })


                                elif LPRL and LPLR and RPRL and RPLR:
                                    # senario where the middle of arc a is overlapped by c
                                    #print '%s middle of arc[%d]:%s' % (col, i, arcs[i]['color'])

                                    # so put c in the middle
                                    arcs[i]['right_side'] = p_left
                                    arcs.insert(i+1, {
                                        'left_side':p_left,
                                        'right_side':p_right,
                                        'd':d2,
                                        'color':col,
                                        'empty':False
                                    })
                                    arcs.insert(i+2, {
                                        'left_side':p_right,
                                        'right_side':a_right,
                                        'd':a_d,
                                        'color':arcs[i]['color'],
                                        'empty':arcs[i]['empty']
                                    })

                                elif LPLL and RPRL and RPLR:
                                    # senario where the left side of arc a is overlapped by c
                                    #print '%s left of arc[%d]:%s' % (col, i, arcs[i]['color'])

                                    # so move arc a's left side in
                                    arcs[i]['left_side'] = p_right

                                    # if arc a is not the first arc and 
                                    # the previous arc is from the same circle
                                    if not first_arc and \
                                    arcs[i-1]['color'] == col and arcs[i-1]['d'] == d2:

                                        # then this is a continuation of the previous arc
                                        # so just update its right side
                                        arcs[i-1]['right_side'] = p_right

                                    # else, this is a new arc
                                    else:

                                        # so insert it starting at the left side of arc a
                                        arcs.insert(i+1, {
                                            'left_side':a_left,
                                            'right_side':p_right,
                                            'd':d2,
                                            'color':col,
                                            'empty':False
                                        })


                                elif LPLL and RPRR:
                                    # senario where all of arc a is overlapped by c
                                    #print '%s all of arc[%d]:%s' % (col, i, arcs[i]['color'])

                                    # if arc a is not the first arc and 
                                    # the previous arc is from the same circle
                                    if not first_arc and \
                                    arcs[i-1]['color'] == col and arcs[i-1]['d'] == d2:

                                        # then this is a continuation of the previous arc
                                        # so just update its right side
                                        arcs[i-1]['right_side'] = a_right
                                        
                                        # and remove this arc
                                        del arcs[i]
                                        i -= 1

                                    # else, this is a new arc
                                    else:
                                        arcs[i]['d'] = d2
                                        arcs[i]['color'] = col
                                        arcs[i]['empty'] = False


        #for a in arcs: print a
        #print ''
        return arcs
    def update_eye_rgb(self, arcs_in_view, eye):

        x, y, r = self.center_x, self.center_y, self.radius
        theta, eye_sep = self.angle, self.eye_position
        if eye == 'left_eye':
            ex, ey = x + r * np.cos(theta - eye_sep), y + r * np.sin(theta - eye_sep)
        else:
            ex, ey = x + r * np.cos(theta + eye_sep), y + r * np.sin(theta + eye_sep)

        total_angle = 2 * self.eye_peripheral_width # all of visual field
                    
        r,g,b = 0.0,0.0,0.0
        for a in arcs_in_view:

            if not a['empty']:

                left_angle  = np.arctan2(ey - a['left_side'][1],  ex - a['left_side'][0])
                right_angle = np.arctan2(ey - a['right_side'][1], ex - a['right_side'][0])
                if left_angle > 0 and right_angle < 0: right_angle += 2*np.pi
                arc_angle = abs(left_angle - right_angle)

                r += (a['color'][0] / 255) * (arc_angle / total_angle)
                g += (a['color'][1] / 255) * (arc_angle / total_angle)
                b += (a['color'][2] / 255) * (arc_angle / total_angle)

        self.visual_input[eye] = [r,g,b]            

    # determine if point C is on the left or right side
    # of line AB from point A's perspective
    def left_side(self, A, B, C):

        # sign((Bx - Ax) * (y - Ay) - (By - Ay) * (x - Ax))
        # + if (x,y) is to the left of line AB, from pt A's perspective,
        # 0 if on the line, and - if to the right

        return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]) <= 0
    def right_side(self, A, B, C):

        # sign((Bx - Ax) * (y - Ay) - (By - Ay) * (x - Ax))
        # + if (x,y) is to the left of line AB, from pt A's perspective,
        # 0 if on the line, and - if to the right

        return (B[0] - A[0]) * (C[1] - A[1]) - (B[1] - A[1]) * (C[0] - A[0]) >= 0


    def update_transform(self):

        x, y = self.center_x, self.center_y
        theta = self.angle
        lwr = self.left_wheel_rotation
        rwr = self.right_wheel_rotation
        wr = self.wheel_radius
        al = self.axle_length

        if lwr == 0 or rwr == 0:

            if lwr == 0 and rwr != 0:
                
                sigma = rwr * wr / al
                new_x = x + (al / 2) * np.sin(sigma) * np.cos(theta) + ((al / 2) * np.cos(sigma) - (al / 2)) * np.sin(theta)
                new_y = y + (al / 2) * np.sin(sigma) * np.sin(theta) + ((al / 2) * np.cos(sigma) - (al / 2)) * np.cos(theta)
                self.pos = (new_x, new_y)
                self.rot -= sigma

            elif lwr != 0 and rwr == 0:

                sigma = lwr * wr / al
                new_x = x + (al / 2) * np.sin(sigma) * np.cos(theta) + ((al / 2) * np.cos(sigma) - (al / 2)) * np.sin(theta)
                new_y = y + (al / 2) * np.sin(sigma) * np.sin(theta) + ((al / 2) * np.cos(sigma) - (al / 2)) * np.cos(theta)
                self.pos = (new_x, new_y)
                self.rot += sigma
        
        elif lwr == rwr:
            
            # calculate and update new position (no change in rotation)
            distance_traveled = lwr * wr
            self.pos = (x + distance_traveled * np.cos(theta), \
                        y + distance_traveled * np.sin(theta))

        else:

            # calculate change in position and rotation
            
            if lwr < rwr:
                radius_of_movement_from_inner_wheel = -al / ((rwr/lwr) - 1)
            elif lwr > rwr:
                radius_of_movement_from_inner_wheel = al / ((lwr/rwr) - 1)

            #print "radius_of_movement_from_inner_wheel:%f" % radius_of_movement_from_inner_wheel
            angle_of_movement = lwr * wr / radius_of_movement_from_inner_wheel

            if radius_of_movement_from_inner_wheel > 0:
                radius_of_movement_from_center = radius_of_movement_from_inner_wheel + al / 2
            else:
                radius_of_movement_from_center = radius_of_movement_from_inner_wheel - al / 2

            #print "radius_of_movement_from_center:%f" % radius_of_movement_from_center
            axle_of_movement_rotation_x = x - radius_of_movement_from_center * np.sin(theta)
            axle_of_movement_rotation_y = y + radius_of_movement_from_center * np.cos(theta)

            #print "old(x,y) = (%f,%f)" % (x, y)
            #print "radius_of_movement_from_center * np.sin(theta) = %f" % (radius_of_movement_from_center * np.sin(theta))
            #print "radius_of_movement_from_center * np.cos(theta) = %f" % (radius_of_movement_from_center * np.cos(theta))

            # axle of rotation
            #pygame.draw.line(surface, [255,0,0], \
            #[axle_of_movement_rotation_x, axle_of_movement_rotation_y], [x,y])

            #print "new(x,y) = (%f,%f)" % \
            #   (axle_of_movement_rotation_x + np.cos(-np.pi/2 + theta + angle_of_movement), \
            #   axle_of_movement_rotation_y + np.sin(-np.pi/2 + theta + angle_of_movement))
            
            # update new transform
            R = radius_of_movement_from_center
            sigma = angle_of_movement
            new_x = x + R * np.sin(sigma) * np.cos(theta) + (R * np.cos(sigma) - R) * np.sin(theta)
            new_y = y + R * np.sin(sigma) * np.sin(theta) + (R * np.cos(sigma) - R) * np.cos(theta)
            
            self.center_x, self.center_y = new_x, new_y
            self.int_center = int(self.center_x), int(self.center_y)
            self.angle += angle_of_movement
            self.out_of_bounds()

            # mx, my = pygame.mouse.get_pos()
            # if mx != SCREEN_SIZE[0]/2:
            #     a = np.arctan(float(my - SCREEN_SIZE[1]/2) / (mx - SCREEN_SIZE[0]/2))
            #     if mx > SCREEN_SIZE[0]/2:
            #         a -= np.pi
            # else:
            #     if my > SCREEN_SIZE[1]/2:
            #         a = -np.pi / 2
            #     else: a = np.pi / 2
            # self.center_x, self.center_y = mx, my
            # self.int_center = int(self.center_x), int(self.center_y)
            #self.angle = a
            #self.out_of_bounds()
            

            # draw direction robot is facing
            #pygame.draw.line(surface, [255,0,0], \
            #[x + 200 * np.cos(theta), y + 200 * np.sin(theta)], [x,y])
    def update_energy(self, model, velocity, angular_velocity):
        """ 
        updates self.energy of a blob based on the distance it moves and an 
        energy loss constant

        Args:
            model (object): contains attributes of the environment
            velocity (float): the distance the blob will move
            angular_velocity (float): the angle the blob will change
        """
        #subtract evergy based on distance moved
        self.energy -= np.abs(velocity) + np.abs(angular_velocity) + ENERGY_LOSS_CONSTANT
        if self.energy < 0:
            self.alive = False
            self.score_int = self.score()
            model.vip_genes.append((self.score_int, self.nn))

            model.blobs.remove(self)

    def process_neural_net(self):
        """
        use blob's neural network to determine velocity and angular velocity

        Returns:
            list containing distance and angle magnitudes
        """
        #assign binary inputs if the blob can see a food or blob object
        #blob_target_input = 0 if self.target_blob == self else 1 
        #food_target_input = 0 if self.target_food == self else 1

        #preprocess neural net inputs
        energy_input = self.energy / 1000. #scale engery between 1 through 0

        #create array containing neural net inputs
        env = np.array(self.visual_input['left_eye'] + self.visual_input['right_eye'] + [energy_input])

        return self.nn.process(env)

    def get_things_within_sight(self, list_of_things):
        """
        determines what objects are within a blob's field of vision

        Args:
            list_of_things (list): a list of objects created using ParentSprite class

        Returns:
            list containing objects in a blob's field of vision
        """
        in_sight = []

        #iterate through all food
        for thing in list_of_things:
            distance = self.get_dist(thing)
            #checks if thing is within blob's radius of sight, and not right on top of it
            #right on top of itself is important when checking if other blobs are within sight
            if distance > 0:
                theta = self.angle - self.angle_between(thing)
                theta = (theta + (2 * np.pi)) % (2 * np.pi)
                #checks if food is within the blob's angle of sight
                if np.fabs(theta) < self.sight_angle:
                    #within sight
                    in_sight.append(thing)

        #return all the things in the list that are within sight
        return in_sight
    

    def eat_food(self, model):
        """ 
        tests whether or not a blob eats food on a given frame. If a blob 
        eats food, remove the food, increase the blob's energy, asexually 
        reproduce based on its neural net dna, and do some population control.

        Args:
            model (object): contains attributes of the environment

        """
        for i in range(len(model.foods)-1, -1, -1):
            if self.intersect(model.foods[i]):
                self.food_eaten += 1
                self.energy += 500

                if self.energy > MAX_ENERGY:
                    self.energy = MAX_ENERGY

                # delete this food
                del model.foods[i]

                # create another food 
                model.foods.append(Food())

                # create another blob with a similar nn
                model.blobs.append(Blob(NN([(1, self.nn)])))

                # kill lowest energy blob if there are more than BLOB_NUM blobs
                #if len(model.blobs) > BLOB_NUM:
                #    energy_list = []
                #    for blob in model.blobs:
                #        energy_list.append(blob.energy)
                #    del model.blobs[np.argmin(energy_list)]


    def score(self):
        """
        gives a blob's score based on: self.food_eaten

        Returns:
            the score of the blob
        """
        return self.food_eaten


    def update(self, model):
        """ 
        Update the blob by calling helper functions.
        """

        # update inputs (visual, audial, etc.)
        self.update_input(model)

        # get current wheel rotations based on neural network
        [self.left_wheel_rotation, self.right_wheel_rotation] = self.process_neural_net()
        
        # update position and energy level based on neural network output
        old_pos   = (self.center_x, self.center_y)
        old_angle = self.angle
        self.update_transform()
        new_pos   = (self.center_x, self.center_y)
        new_angle = self.angle
        displacement = math.sqrt((new_pos[0] - old_pos[0]) ** 2 + (new_pos[1] - new_pos[1]) ** 2)
        angular_displacement = new_angle - old_angle
        self.update_energy(model, displacement, angular_displacement)

        # update color of blob
        #self.update_color()

        # interact with food objects
        self.eat_food(model)

        # re-assign targets
        #self.target_closest_blob(self.get_things_within_sight(model.blobs))
        #self.target_closest_food(self.get_things_within_sight(model.foods))

