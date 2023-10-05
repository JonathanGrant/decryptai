import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';


const URL = "http://127.0.0.1:5000"

const GameAppBar = ({playerName}) => {

  return (
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" style={{ flexGrow: 1 }}>
            wAIvelength
          </Typography>
          <Box>
            <Typography variant="h6">
              {`Player: ${playerName}`}
            </Typography>
          </Box>
        </Toolbar>
      </AppBar>
  );
};

export default GameAppBar;
