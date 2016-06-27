module.exports = function(grunt) {
    var DEV = grunt.option('dev') || false;

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        dir: {
            static        : './graphdash',
            static_sass   : '<%= dir.static %>/assets/sass',
            static_css    : '<%= dir.static %>/assets/css',
            static_coffee : '<%= dir.static %>/assets/coffee',
            static_js     : '<%= dir.static %>/assets/js',
        },
        shell: {
            reloadGunicorn: {
                options: { stdout: true },
                command: 'cat *.pid | xargs kill -HUP'
            }
        },
        sass: {
            sass: {
                /* Not recursive, we do not want to compile dependencies
                 * stored in sub directories */
                options: {
                    sourcemap : 'auto',
                    style     : DEV ? 'expanded' : 'compressed'
                },
                expand : true,
                src    : '*.sass',
                cwd    : '<%= dir.static_sass %>',
                dest   : '<%= dir.static_css %>',
                ext    : '.css'
            },
        },
        coffee: {
            coffee: {
                options: {
                    sourceMap: true
                },
                expand : true,
                src    : '**/*.coffee',
                cwd    : '<%= dir.static_coffee %>',
                dest   : '<%= dir.static_js %>',
                ext    : '.js'
            },
        },
        jshint: {
            gruntfile: 'Gruntfile.js',
            js: {
                files: [{
                    expand: true,
                    src   : ['**/*.js', '!**/*.min.js'],
                    cwd   : '<%= dir.static_js %>'
                }],
                options: {
                    globals: {
                        jQuery  : true,
                        console : true,
                        module  : true,
                        document: true
                    }
                }
            }
        },
        uglify: {
            js: {
                options: {
                    sourceMap   : true,
                    sourceMapIn : function(name) {
                        return name + '.map';
                    },
                    // report: 'gzip', // display gzip stats
                    beautify : DEV ? true : false,
                    mangle   : DEV ? false : true,
                },
                files: [{
                    expand: true,
                    src   : ['**/*.js', '!**/*.min.js'],
                    cwd   : '<%= dir.static_js %>',
                    dest  : '<%= dir.static_js %>',
                    ext   : '.min.js'
                }]
            }
        },
        watch: {
            gruntfile: {
                files: 'Gruntfile.js',
                tasks: 'default',
            },
            sass: {
                files: '**/*.sass',
                tasks: ['sass'],
            },
            coffee: {
                files: '**/*.coffee',
                tasks: ['coffee'],
            },
            js: {
                files: ['**/*.js', '!**/*.min.js'],
                tasks: ['jshint', 'uglify'],
            },
            py: {
                files: '**/*.py',
                tasks: ['shell'],
            },
            livereload: {
                files: ['**/*.html', '**/*.js', '**/*.css', '**/*.py'],
                options: { livereload: true },
            }
        }
    });

    grunt.loadNpmTasks('grunt-shell');
    grunt.loadNpmTasks('grunt-contrib-sass');
    grunt.loadNpmTasks('grunt-contrib-coffee');
    grunt.loadNpmTasks('grunt-contrib-jshint');
    grunt.loadNpmTasks('grunt-contrib-uglify');
    grunt.loadNpmTasks('grunt-contrib-watch');

    grunt.registerTask('js', ['coffee', 'jshint', 'uglify']);
    grunt.registerTask('default', ['sass', 'js']);
};
